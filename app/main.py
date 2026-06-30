import csv
import io
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app import database as db
from app.database import init_db
from app.line_handlers import handle_webhook

app = FastAPI(title="Personal Expense Tracker LINE Bot")

# Path to the rich menu background image (bundled with the repo)
_RICH_MENU_IMAGE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rich_menu.jpg")


@app.on_event("startup")
def startup():
    """Initialize the database on first launch."""
    init_db()
    print("✅ Database initialized.")


@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    """Health check. Also reports OCR/QR readiness so a single GET / tells you
    whether slip reading will work (no need to open /ocr-status separately).
    Accepts HEAD too, so Render's health probe doesn't log 405s."""
    from app.ocr_service import get_status
    ocr = get_status()
    return {
        "status": "ok",
        "message": "Expense Tracker Bot is running.",
        "ocr_available": ocr.get("available"),
        "ocr_lang": ocr.get("lang"),
        "qr_fallback": ocr.get("qr_fallback"),
    }


@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    """Health check for UptimeRobot / monitoring / Render probe."""
    return {"status": "healthy"}


@app.post("/webhook")
async def webhook(request: Request):
    """LINE webhook callback endpoint."""
    return await handle_webhook(request)


@app.get("/ocr-status")
async def ocr_status():
    """Diagnostic: check if Tesseract is installed and working."""
    from app.ocr_service import get_status
    return JSONResponse(get_status())


@app.get("/export/{user_id}.csv")
async def export_csv(user_id: str):
    """Download all of a user's transactions as a CSV file."""
    txns = db.get_all_transactions(user_id)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "description", "category", "amount", "source"])
    for t in txns:
        writer.writerow([
            str(t["created_at"])[:10],
            t["description"] or "",
            t["category"],
            t["amount"],
            t["source"],
        ])
    buf.seek(0)

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="expenses_{user_id}.csv"'},
    )


@app.get("/setup-rich-menu")
async def setup_rich_menu_endpoint():
    """
    One-time setup: creates the 6-button rich menu in LINE and sets it as default.
    Visit this URL in your browser after deploying:
      https://withexpenese.onrender.com/setup-rich-menu
    """
    from app.rich_menu import setup_rich_menu
    image_path = _RICH_MENU_IMAGE if os.path.exists(_RICH_MENU_IMAGE) else None
    result = setup_rich_menu(image_path=image_path)
    if result["ok"]:
        return JSONResponse({"status": "✅ Rich menu created", "richMenuId": result["richMenuId"]})
    return JSONResponse({"status": "❌ Failed", "error": result.get("error")}, status_code=500)
