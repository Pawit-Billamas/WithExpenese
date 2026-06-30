"""OCR via Google Gemini Vision API (free tier - 1500 requests/day)."""
import os
import base64
import json
import urllib.request
import urllib.error
from datetime import datetime


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent?key={key}"
)


async def ocr_slip_image(image_bytes: bytes) -> dict:
    """
    Send a payment slip image to Gemini Vision and extract the total amount.
    Returns {"amount": float_or_none, "raw_text": str}.
    Falls back gracefully if API key is missing or call fails.
    """
    if not GEMINI_API_KEY or not image_bytes:
        return {"amount": None, "raw_text": ""}

    try:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        payload = json.dumps({
            "contents": [{
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": b64,
                        }
                    },
                    {
                        "text": (
                            "This is a Thai payment slip or receipt. "
                            "Extract ONLY the final total amount paid in Thai Baht (THB). "
                            "Reply with ONLY a plain number, no currency symbol, no commas, no text. "
                            "If you cannot find a clear amount, reply with the word: NONE"
                        )
                    },
                ]
            }]
        }).encode("utf-8")

        url = GEMINI_URL.format(key=GEMINI_API_KEY)
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        raw = (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
            .strip()
        )

        if raw.upper() == "NONE" or not raw:
            return {"amount": None, "raw_text": raw}

        # Clean and parse the number
        cleaned = raw.replace(",", "").replace(" ", "")
        amount = float(cleaned)
        return {"amount": amount, "raw_text": raw}

    except (urllib.error.URLError, ValueError, KeyError, IndexError) as e:
        print(f"[OCR Error] {e}")
        return {"amount": None, "raw_text": ""}