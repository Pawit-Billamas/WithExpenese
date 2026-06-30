import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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


@app.get("/")
async def root():
    """Health check."""
    return {"status": "ok", "message": "Expense Tracker Bot is running."}


@app.get("/health")
async def health():
    """Health check for UptimeRobot / monitoring."""
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
