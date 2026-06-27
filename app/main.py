import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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


# ── Run directly for local development ──────────────────────────────

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
