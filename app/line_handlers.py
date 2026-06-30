import io
import csv
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
from app.ocr_service import ocr_slip_image

configuration = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(channel_secret=settings.LINE_CHANNEL_SECRET)


def get_image_content(message_id: str) -> bytes:
    """Download image bytes from LINE (synchronous, no extra deps)."""
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read()


def build_category_quick_reply(categories: list[str]) -> QuickReply:
    items = []
    for cat in categories[:10]:
        items.append(QuickReplyItem(action=MessageAction(label=cat, text=cat)))
    items.append(QuickReplyItem(action=MessageAction(label="➕ New Category", text="➕ New Category")))
    return QuickReply(items=items)


def build_budget_warning(user_id: str, current_amount: float) -> str:
    budget = settings.MONTHLY_BUDGET
    if budget <= 0:
        return ""
    monthly_total = db.get_monthly_total(user_id) + current_amount
    pct = (monthly_total / budget) * 100
    if pct >= 100:
        return f"\n\n⚠️ **Budget Exceeded!** Month total: {monthly_total:,.0f} / {budget:,.0f} THB ({pct:.0f}%)"
    elif pct >= 80:
        return f"\n\n⚠️ **Budget Alert ({pct:.0f}%)** Month total: {monthly_total:,.0f} / {budget:,.0f} THB"
    elif pct >= 50:
        return f"\nℹ️ Month total: {monthly_total:,.0f} / {budget:,.0f} THB ({pct:.0f}%)"
    return ""


async def handle_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")
    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        return {"status": "invalid signature"}
    return {"status": "ok"}


@handler.add(FollowEvent)
def handle_follow(event: FollowEvent):
    welcome = (
        "👋 Welcome to FREE Expense Tracker Bot!\n\n"
        "📸 Send me a payment slip photo\n"
        "💰 Type: cash [amount] [description]\n\n"
        "Commands: recent, summary, categories, export"
    )
    _reply(event.reply_token, [TextMessage(text=welcome)])


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event: MessageEvent):
    user_id = event.source.user_id
    text = event.message.text.strip()
    reply_token = event.reply_token

    cash_match = re.match(r"^cash\s+(\d+(?:\.\d{1,2})?)\s*(.*)?$", text, re.IGNORECASE)
    if cash_match:
        _handle_cash_command(user_id, reply_token, cash_match)
        return True

    edit_match = re.match(r"^edit\s+(\d+(?:\.\d{1,2})?)$", text, re.IGNORECASE)
    if edit_match:
        _handle_edit_command(user_id, reply_token, edit_match)
        return True

    if text.lower() == "export":
        _handle_export(user_id, reply_token)
        return True

    if text.lower() == "recent":
        _handle_recent(user_id, reply_token)
        return True

    if text.lower() == "summary":
        _handle_summary(user_id, reply_token)
        return True

    if text.lower() == "categories":
        _handle_list_categories(user_id, reply_token)
        return True

    if text.lower() == "log cash":
        _reply(reply_token, [TextMessage(text="To log cash: type `cash [amount] [description]`\nExample: cash 120 lunch")])
        return True

    if text.lower() == "help":
        help_text = (
            "📚 **Expense Tracker Commands**\n\n"
            "💰 Log Expense:\n"
            "• cash [amount] [description]\n"
            "• Example: cash 120 lunch\n\n"
            "📸 Send Slip Photo:\n"
            "• Bot reads amount automatically\n\n"
            "📊 View Data:\n"
            "• recent - Last 5 transactions\n"
            "• summary - Monthly breakdown\n"
            "• export - Download all data\n"
            "• categories - List categories\n\n"
            "✏️ Edit Amount:\n"
            "• edit [amount]\n"
            "• Example: edit 150"
        )
        _reply(reply_token, [TextMessage(text=help_text)])
        return True

    pending = db.get_pending(user_id)
    if pending and pending["state"] == "awaiting_new_category_name":
        _finalize_new_category(user_id, reply_token, pending, text)
        return True

    if pending and pending["state"] == "awaiting_category":
        _handle_category_selection(user_id, reply_token, pending, text)
        return True

    _reply(reply_token, [TextMessage(text="Commands:\n• cash [amount] [desc]\n• recent\n• summary\n• export\n• categories")])
    return True


@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event: MessageEvent):
    """Process slip image - manual amount entry (no OCR)."""
    user_id = event.source.user_id
    reply_token = event.reply_token
    db.add_pending(user_id, 0, "Slip photo", "", "Awaiting manual amount")
    _reply(reply_token, [TextMessage(
        text="📸 Image received!\n\nType amount:\nedit [amount]\n\nExample: edit 140"
    )])




def _handle_cash_command(user_id: str, reply_token: str, match: re.Match):
    amount = float(match.group(1))
    desc = match.group(2) or ""
    pending = db.get_pending(user_id)
    if pending:
        db.delete_pending(user_id)
    db.add_pending(user_id, amount, desc, "")
    cats = db.get_categories()
    qr = build_category_quick_reply(cats)
    _reply(reply_token, [TextMessage(text=f"💰 Cash: {amount:,.0f} THB. Select category:", quick_reply=qr)])


def _handle_edit_command(user_id: str, reply_token: str, match: re.Match):
    pending = db.get_pending(user_id)
    if not pending:
        _reply(reply_token, [TextMessage(text="❌ No pending transaction.")])
        return
    new_amount = float(match.group(1))
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE pending_transactions SET amount = %s WHERE id = %s", (new_amount, pending["id"]))
    conn.commit()
    cursor.close()
    conn.close()
    cats = db.get_categories()
    qr = build_category_quick_reply(cats)
    _reply(reply_token, [TextMessage(text=f"✅ Amount: {new_amount:,.0f} THB. Select category:", quick_reply=qr)])


def _handle_export(user_id: str, reply_token: str):
    transactions = db.get_all_transactions(user_id)
    if not transactions:
        _reply(reply_token, [TextMessage(text="📭 No transactions.")])
        return
    lines = [f"📊 {len(transactions)} transactions:\n"]
    for t in transactions[:20]:
        lines.append(f"{t['amount']:,.0f} THB — {t['category']} — {t['created_at'][:10]}")
    _reply(reply_token, [TextMessage(text="\n".join(lines))])


def _handle_recent(user_id: str, reply_token: str):
    transactions = db.get_all_transactions(user_id)
    if not transactions:
        _reply(reply_token, [TextMessage(text="📭 No transactions.")])
        return
    lines = ["📋 Recent:"]
    for t in transactions[:5]:
        lines.append(f"• {t['amount']:,.0f} THB — {t['category']}")
    _reply(reply_token, [TextMessage(text="\n".join(lines))])


def _handle_summary(user_id: str, reply_token: str):
    monthly = db.get_monthly_total(user_id)
    rows = db.get_monthly_summary(user_id)
    if not rows:
        _reply(reply_token, [TextMessage(text="📭 No transactions.")])
        return
    lines = [f"📊 Total: {monthly:,.0f} THB\n"]
    for r in rows:
        lines.append(f"• {r['category']}: {r['total']:,.0f}")
    budget = settings.MONTHLY_BUDGET
    if budget > 0:
        pct = (monthly / budget) * 100
        lines.append(f"\nBudget: {pct:.0f}%")
    _reply(reply_token, [TextMessage(text="\n".join(lines))])


def _handle_list_categories(user_id: str, reply_token: str):
    cats = db.get_categories()
    if not cats:
        _reply(reply_token, [TextMessage(text="📭 No categories.")])
        return
    lines = ["📂 Categories:"]
    for i, c in enumerate(cats, 1):
        lines.append(f"{i}. {c}")
    _reply(reply_token, [TextMessage(text="\n".join(lines))])


def _finalize_new_category(user_id: str, reply_token: str, pending: dict, text: str):
    new_cat = text.strip()
    if not new_cat:
        _reply(reply_token, [TextMessage(text="Enter a valid name.")])
        return
    if db.add_category(new_cat):
        db.add_transaction(
            user_id=user_id, amount=pending["amount"], category=new_cat,
            description=pending["description"], image_url=pending["image_url"],
            source="slip" if pending["image_url"] else "cash"
        )
        db.delete_pending(user_id)
        warning = build_budget_warning(user_id, pending["amount"])
        _reply(reply_token, [TextMessage(text=f"✅ Added '{new_cat}' → {pending['amount']:,.0f} THB{warning}")])
    else:
        _reply(reply_token, [TextMessage(text=f"❌ '{new_cat}' exists.")])


def _handle_category_selection(user_id: str, reply_token: str, pending: dict, text: str):
    cats = db.get_categories()
    if text in cats:
        db.add_transaction(
            user_id=user_id, amount=pending["amount"], category=text,
            description=pending["description"], image_url=pending["image_url"],
            source="slip" if pending["image_url"] else "cash"
        )
        db.delete_pending(user_id)
        warning = build_budget_warning(user_id, pending["amount"])
        _reply(reply_token, [TextMessage(text=f"✅ {pending['amount']:,.0f} THB → {text}{warning}")])
    elif text == "➕ New Category":
        db.update_pending_state(user_id, "awaiting_new_category_name")
        _reply(reply_token, [TextMessage(text="Type new category:")])
    else:
        _reply(reply_token, [TextMessage(text="❌ Choose from list.")])


async def _process_image(user_id: str, message_id: str, reply_token: str):
    try:
        image_bytes = await get_image_content(message_id)
        _reply(reply_token, [TextMessage(text="📸 Processing slip... ⏳")])
        
        # OCR the image
        ocr_result = await ocr_slip_image(image_bytes)
        amount = ocr_result.get("amount")
        
        if amount and amount > 0:
            # Amount found! Show categories immediately
            db.add_pending(user_id, amount, "Payment slip", "", ocr_result.get("raw_text", ""))
            cats = db.get_categories()
            qr = build_category_quick_reply(cats)
            _reply(reply_token, [TextMessage(
                text=f"✅ Found amount: {amount:,.0f} THB\n\nSelect category:",
                quick_reply=qr
            )])
        else:
            # Couldn't read amount, ask user to enter manually
            db.add_pending(user_id, 0, "Payment slip", "", ocr_result.get("raw_text", ""))
            _reply(reply_token, [TextMessage(
                text=f"🤔 Couldn't read amount clearly.\n\nType: edit [amount]\nExample: edit 140"
            )])
    except Exception as e:
        _reply(reply_token, [TextMessage(text=f"❌ Error: {e}")])


def _reply(reply_token: str, messages: list):
    try:
        with ApiClient(configuration) as api_client:
            api_instance = MessagingApi(api_client)
            api_instance.reply_message(ReplyMessageRequest(reply_token=reply_token, messages=messages))
    except Exception as e:
        print(f"[Reply Error] {e}")
