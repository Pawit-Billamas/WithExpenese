"""Lightweight stub - no heavy dependencies for PythonAnywhere."""
from datetime import datetime


async def ocr_slip_image(image_bytes=None):
    return {
        "amount": None,
        "description": "Manual entry",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "raw_text": "",
    }