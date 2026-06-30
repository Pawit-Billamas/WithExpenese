import re
import urllib.request
from fastapi import Request
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    QuickReply,
    QuickReplyItem,
    MessageAction,
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent,
    FollowEvent,
)
from linebot.exceptions import InvalidSignatureError

from app.config import settings
from app import database as db
from app.ocr_service import ocr_slip_image_sync

configuration = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(channel_secret=settings.LINE_CHANNEL_SECRET)


# ── Helpers ──────────────────────────────────────────────────────────

def _get_image_bytes(message_id: str) -> bytes:
    """Download image bytes from LINE servers."""
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def _build_category_quick_reply(categories: list[str]) -> QuickReply:
    items = [QuickReplyItem(action=MessageAction(label=c, text=c)) for c in categories[:10]]
    items.append(QuickReplyItem(action=MessageAction(label="➕ New", text="➕ New Category")))
    return QuickReply(items=items)


def _budget_warning(user_id: str, added: float) -> str:
    budget = settings.MONTHLY_BUDGET
    if budget <= 0:
        return ""
    total = db.get_monthly_total(user_id) + added
    pct = (total / budget) * 100
    if pct >= 100:
        return f"\n\n⚠️ Budget exceeded! {total:,.0f} / {budget:,.0f} THB ({pct:.0f}%)"
    if pct >= 80:
        return f"\n\n⚠️ Budget {pct:.0f}% used — {total:,.0f} / {budget:,.0f} THB"
    if pct >= 50:
        return f"\nℹ️ {total:,.0f} / {budget:,.0f} THB ({pct:.0f}%)"
    return ""


def _reply(reply_token: str, messages: list):
    try:
        with ApiClient(configuration) as api_client:
            MessagingApi(api_client).reply_message(
                ReplyMessageRequest(reply_token=reply_token, messages=messages)
            )
    except Exception as e:
        print(f"[Reply Error] {e}")


# ── Webhook entry point ───────────────────────────────────────────────

async def handle_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")
    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        return {"status": "invalid signature"}
    return {"status": "ok"}


# ── EVENT: Follow ─────────────────────────────────────────────────────

@handler.add(FollowEvent)
def handle_follow(event: FollowEvent):
    _reply(event.reply_token, [TextMessage(text=(
        "👋 Welcome to Expense Tracker!\n\n"
        "📸 Send a slip photo → I'll read the amount\n"
        "💰 Type: cash [amount] → I'll ask what it's for\n\n"
        "📊 Commands: recent · summary · categories · export · help"
    ))])


# ── EVENT: Text message ───────────────────────────────────────────────

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event: MessageEvent):
    user_id = event.source.user_id
    text = event.message.text.strip()
    token = event.reply_token

    # ── Built-in commands ──────────────────────────────────────────
    if text.lower() == "help":
        _reply(token, [TextMessage(text=(
            "📚 Commands\n\n"
            "💰 cash [amount] — log cash expense\n"
            "   Example: cash 150\n\n"
            "📸 Send a slip photo — auto-reads amount\n\n"
            "📋 recent — last 5 transactions\n"
            "📊 summary — monthly breakdown\n"
            "📂 categories — list categories\n"
            "📤 export — show all transactions\n"
            "✏️ edit [amount] — fix amount on pending slip"
        ))])
        return

    if text.lower() == "recent":
        _handle_recent(user_id, token)
        return

    if text.lower() == "summary":
        _handle_summary(user_id, token)
        return

    if text.lower() == "categories":
        _handle_categories(user_id, token)
        return

    if text.lower() == "export":
        _handle_export(user_id, token)
        return

    # ── cash [amount] ──────────────────────────────────────────────
    cash_match = re.match(r"^cash\s+(\d+(?:\.\d{1,2})?)$", text, re.IGNORECASE)
    if cash_match:
        _start_cash(user_id, token, float(cash_match.group(1)))
        return

    # ── edit [amount] (fix amount on a pending slip) ───────────────
    edit_match = re.match(r"^edit\s+(\d+(?:\.\d{1,2})?)$", text, re.IGNORECASE)
    if edit_match:
        _handle_edit(user_id, token, float(edit_match.group(1)))
        return

    # ── Pending-state machine ──────────────────────────────────────
    pending = db.get_pending(user_id)

    if pending and pending["state"] == "awaiting_description":
        _handle_description_input(user_id, token, pending, text)
        return

    if pending and pending["state"] == "awaiting_category":
        _handle_category_selection(user_id, token, pending, text)
        return

    if pending and pending["state"] == "awaiting_new_category_name":
        _finalize_new_category(user_id, token, pending, text)
        return

    _reply(token, [TextMessage(text="Type 'help' to see commands.")])


# ── EVENT: Image (slip photo) ─────────────────────────────────────────

@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event: MessageEvent):
    """
    Download slip, run Tesseract OCR.
    If amount found  → ask for item name.
    If amount NOT found → show raw OCR snippet so user can debug, then ask for manual entry.
    """
    user_id = event.source.user_id
    token = event.reply_token
    message_id = event.message.id

    try:
        image_bytes = _get_image_bytes(message_id)
        # Tesseract is blocking CPU work — call it synchronously.
        # (Spinning up a nested event loop here crashes inside uvicorn's
        #  already-running loop: "Cannot run the event loop while another
        #  loop is running".)
        ocr_result = ocr_slip_image_sync(image_bytes)
    except Exception as e:
        print(f"[Image Download/OCR Error] {e}")
        ocr_result = {"amount": None, "raw_text": str(e), "debug_lines": []}

    amount = ocr_result.get("amount")

    # Clear any stale pending
    db.delete_pending(user_id)

    if amount and amount > 0:
        db.add_pending(user_id, amount, "", "", ocr_result.get("raw_text", ""))
        db.update_pending_state(user_id, "awaiting_description")
        _reply(token, [TextMessage(
            text=f"📸 Slip read!\n💰 Amount: {amount:,.0f} THB\n\nWhat's the item name?\n(e.g. coffee, taxi, lunch)"
        )])
    else:
        # Show first 10 lines of what Tesseract actually read so we can debug
        debug_lines = ocr_result.get("debug_lines", [])
        preview = "\n".join(ln for ln in debug_lines[:12] if ln.strip()) or "(nothing read)"
        db.add_pending(user_id, 0, "", "", "")
        _reply(token, [TextMessage(
            text=(
                "📸 Got the slip — couldn't detect the amount.\n\n"
                f"🔍 OCR read:\n{preview}\n\n"
                "Please type the amount manually:\nedit [amount]\nExample: edit 200"
            )
        )])


# ── Flow steps ────────────────────────────────────────────────────────

def _start_cash(user_id: str, token: str, amount: float):
    """User typed 'cash 150' — clear any pending, save amount, ask for item name."""
    db.delete_pending(user_id)
    db.add_pending(user_id, amount, "", "", "")
    db.update_pending_state(user_id, "awaiting_description")
    _reply(token, [TextMessage(
        text=f"💰 {amount:,.0f} THB\n\nWhat's the item name?\n(e.g. iced coffee, taxi, lunch)"
    )])


def _handle_edit(user_id: str, token: str, new_amount: float):
    """User typed 'edit 140' — update amount on pending slip, ask for item name."""
    pending = db.get_pending(user_id)
    if not pending:
        _reply(token, [TextMessage(text="❌ No pending transaction. Send a slip first.")])
        return
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE pending_transactions SET amount = %s WHERE id = %s",
        (new_amount, pending["id"])
    )
    conn.commit()
    cursor.close()
    conn.close()
    db.update_pending_state(user_id, "awaiting_description")
    _reply(token, [TextMessage(
        text=f"✅ Amount set: {new_amount:,.0f} THB\n\nWhat's the item name?\n(e.g. iced coffee, taxi, lunch)"
    )])


def _handle_description_input(user_id: str, token: str, pending: dict, text: str):
    """User typed an item name — save it, show category picker."""
    description = text.strip()
    if not description:
        _reply(token, [TextMessage(text="Please type a name for this expense.")])
        return
    # Save description into the pending row
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE pending_transactions SET description = %s, state = 'awaiting_category' WHERE id = %s",
        (description, pending["id"])
    )
    conn.commit()
    cursor.close()
    conn.close()
    cats = db.get_categories()
    qr = _build_category_quick_reply(cats)
    _reply(token, [TextMessage(
        text=f"📝 \"{description}\" — {pending['amount']:,.0f} THB\n\nPick a category:",
        quick_reply=qr
    )])


def _handle_category_selection(user_id: str, token: str, pending: dict, text: str):
    """User picked a category (or tapped ➕ New)."""
    cats = db.get_categories()
    if text in cats:
        db.add_transaction(
            user_id=user_id,
            amount=pending["amount"],
            category=text,
            description=pending["description"],
            image_url=pending.get("image_url", ""),
            source="slip" if pending.get("image_url") else "cash",
        )
        db.delete_pending(user_id)
        warning = _budget_warning(user_id, pending["amount"])
        _reply(token, [TextMessage(
            text=f"✅ Saved!\n📝 {pending['description']}\n💰 {pending['amount']:,.0f} THB → {text}{warning}"
        )])
    elif text == "➕ New Category":
        db.update_pending_state(user_id, "awaiting_new_category_name")
        _reply(token, [TextMessage(text="Type the new category name:")])
    else:
        cats = db.get_categories()
        qr = _build_category_quick_reply(cats)
        _reply(token, [TextMessage(text="Please pick a category from the list:", quick_reply=qr)])


def _finalize_new_category(user_id: str, token: str, pending: dict, text: str):
    """User typed a new category name."""
    new_cat = text.strip()
    if not new_cat:
        _reply(token, [TextMessage(text="Please enter a valid category name.")])
        return
    if db.add_category(new_cat):
        db.add_transaction(
            user_id=user_id,
            amount=pending["amount"],
            category=new_cat,
            description=pending["description"],
            image_url=pending.get("image_url", ""),
            source="slip" if pending.get("image_url") else "cash",
        )
        db.delete_pending(user_id)
        warning = _budget_warning(user_id, pending["amount"])
        _reply(token, [TextMessage(
            text=f"✅ Saved!\n📝 {pending['description']}\n💰 {pending['amount']:,.0f} THB → {new_cat}{warning}"
        )])
    else:
        _reply(token, [TextMessage(text=f"❌ '{new_cat}' already exists. Pick from the list.")])


# ── View commands ─────────────────────────────────────────────────────

def _handle_recent(user_id: str, token: str):
    txns = db.get_all_transactions(user_id)
    if not txns:
        _reply(token, [TextMessage(text="📭 No transactions yet.")])
        return
    lines = ["📋 Recent 5 transactions:"]
    for t in txns[:5]:
        date = str(t["created_at"])[:10]
        lines.append(f"• {t['description'] or t['category']} — {t['amount']:,.0f} THB [{t['category']}] {date}")
    _reply(token, [TextMessage(text="\n".join(lines))])


def _handle_summary(user_id: str, token: str):
    monthly = db.get_monthly_total(user_id)
    rows = db.get_monthly_summary(user_id)
    if not rows:
        _reply(token, [TextMessage(text="📭 No transactions this month.")])
        return
    lines = [f"📊 This month: {monthly:,.0f} THB\n"]
    for r in rows:
        lines.append(f"• {r['category']}: {r['total']:,.0f} THB ({r['count']} items)")
    budget = settings.MONTHLY_BUDGET
    if budget > 0:
        pct = (monthly / budget) * 100
        lines.append(f"\n📈 Budget: {pct:.0f}% used ({monthly:,.0f} / {budget:,.0f} THB)")
    _reply(token, [TextMessage(text="\n".join(lines))])


def _handle_categories(user_id: str, token: str):
    cats = db.get_categories()
    if not cats:
        _reply(token, [TextMessage(text="📭 No categories yet.")])
        return
    lines = ["📂 Categories:"] + [f"{i}. {c}" for i, c in enumerate(cats, 1)]
    _reply(token, [TextMessage(text="\n".join(lines))])


def _handle_export(user_id: str, token: str):
    txns = db.get_all_transactions(user_id)
    if not txns:
        _reply(token, [TextMessage(text="📭 No transactions.")])
        return
    lines = [f"📤 {len(txns)} transactions:\n"]
    for t in txns[:20]:
        date = str(t["created_at"])[:10]
        name = t["description"] or "-"
        lines.append(f"{date} | {name} | {t['amount']:,.0f} THB | {t['category']}")
    if len(txns) > 20:
        lines.append(f"... and {len(txns) - 20} more")
    _reply(token, [TextMessage(text="\n".join(lines))])
