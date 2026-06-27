from fastapi import FastAPI, Request

from app.database import init_db
from app.line_handlers import handle_webhook

app = FastAPI(title="Personal Expense Tracker LINE Bot")


@app.on_event("startup")
def startup():
    """Initialize the database on first launch."""
    init_db()
    print("✅ Database initialized.")


@app.get("/")
async def root():
    """Health check."""
    return {"status": "ok", "message": "Expense Tracker Bot is running."}


@app.post("/webhook")
async def webhook(request: Request):
    """LINE webhook callback endpoint."""
    return await handle_webhook(request)


@app.get("/health")
async def health():
    """Health check for monitoring."""
    return {"status": "healthy"}
