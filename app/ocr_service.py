"""
OCR using Tesseract — 100% free, no API keys, no AI.
Tesseract is installed on Render via the buildCommand in render.yaml.
"""
import re
import io

try:
    from PIL import Image, ImageEnhance, ImageFilter
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


def _preprocess(image_bytes: bytes):
    """Convert to grayscale and boost contrast for better OCR accuracy."""
    img = Image.open(io.BytesIO(image_bytes)).convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)
    return img


def _extract_amount(text: str) -> float | None:
    """
    Parse the total/paid amount from raw OCR text of a Thai payment slip.
    Tries keyword-anchored patterns first, then falls back to largest plausible number.
    """
    # Pattern 1: number right after a Thai/English total keyword
    keyword_pattern = re.compile(
        r'(?:จำนวนเงิน|ยอดรวม|ยอดชำระ|ยอดที่ต้องชำระ|รวม|ยอด|Total|Amount|Grand\s*Total|Net\s*Total)'
        r'\s*[:\s]*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)',
        re.IGNORECASE,
    )
    # Pattern 2: number followed by บาท / THB / ฿
    currency_pattern = re.compile(
        r'([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)\s*(?:บาท|THB|฿)',
        re.IGNORECASE,
    )
    # Pattern 3: fallback — any number between 1 and 99999
    fallback_pattern = re.compile(
        r'\b([0-9]{2,5}(?:\.[0-9]{1,2})?)\b'
    )

    candidates = []

    for pattern in (keyword_pattern, currency_pattern, fallback_pattern):
        for match in pattern.finditer(text):
            raw = match.group(1).replace(",", "")
            try:
                val = float(raw)
                if 1.0 <= val <= 99999.0:
                    candidates.append(val)
            except ValueError:
                continue
        if candidates:
            # Return the largest candidate from this priority level
            return max(candidates)

    return None


async def ocr_slip_image(image_bytes: bytes) -> dict:
    """
    Run Tesseract OCR on the slip image and return the extracted amount.
    Returns {"amount": float_or_none, "raw_text": str}.
    """
    if not TESSERACT_AVAILABLE or not image_bytes:
        return {"amount": None, "raw_text": ""}

    try:
        img = _preprocess(image_bytes)

        # Run Tesseract with Thai + English language pack
        raw_text = pytesseract.image_to_string(img, lang="tha+eng", config="--psm 6")
        print(f"[OCR raw text]\n{raw_text}")

        amount = _extract_amount(raw_text)
        return {"amount": amount, "raw_text": raw_text}

    except Exception as e:
        print(f"[OCR Error] {e}")
        return {"amount": None, "raw_text": ""}