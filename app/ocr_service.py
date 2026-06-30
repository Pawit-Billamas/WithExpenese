"""
OCR using Tesseract with English only — no Thai language pack required.
Numbers like 200.00 and 100.00 are ASCII digits, readable by any Tesseract install.
Strategy: find the largest decimal number (X.XX) that is > 0 and ≤ 99999.
The fee is always 0.00 which is automatically excluded (value = 0).
"""
import re
import io
import shutil

try:
    from PIL import Image, ImageEnhance, ImageFilter
    import pytesseract

    # Find tesseract binary — Render installs it at /usr/bin/tesseract
    _tess = shutil.which("tesseract") or "/usr/bin/tesseract"
    pytesseract.pytesseract.tesseract_cmd = _tess

    # Quick self-test at startup
    _version = pytesseract.get_tesseract_version()
    TESSERACT_AVAILABLE = True
    print(f"[OCR] Tesseract {_version} ready at: {_tess}")

except Exception as _e:
    TESSERACT_AVAILABLE = False
    _SETUP_ERROR = str(_e)
    print(f"[OCR] Tesseract NOT available: {_e}")


# ── Image preprocessing ───────────────────────────────────────────────

def _preprocess(image_bytes: bytes):
    """
    Scale 2× + aggressive binarise to kill watermarks
    (MyMo repeated 'mymo' pattern, KBank building).
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # 2× upscale — Tesseract accuracy improves significantly
    w, h = img.size
    img = img.resize((w * 2, h * 2), Image.LANCZOS)

    # Grayscale → heavy contrast boost → hard threshold
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(3.5)
    img = ImageEnhance.Brightness(img).enhance(1.2)
    img = img.point(lambda p: 0 if p < 160 else 255)
    img = img.filter(ImageFilter.SHARPEN)

    return img


# ── Amount extraction (no Thai needed) ───────────────────────────────

# Matches amounts like 200.00 / 1,500.00 — exactly 1 or 2 decimal places
_DECIMAL = re.compile(r"\b(\d{1,6}(?:,\d{3})*\.\d{2})\b")


def _extract_amount(text: str) -> float | None:
    """
    Find the transfer amount from raw OCR text.

    Key observations (both MyMo & KBank slips):
    - The actual transfer amount is a non-zero decimal: 200.00, 100.00
    - The fee is always 0.00  → excluded because float("0.00") == 0.0 < 1.0
    - Reference/account numbers have no decimal point → excluded by _DECIMAL pattern
    - Dates/times use colons (15:04) or are integers → not matched by _DECIMAL

    So: take the LARGEST decimal number ≥ 1.0 and ≤ 99999 → that is the amount.
    """
    candidates = []
    for m in _DECIMAL.finditer(text):
        raw = m.group(1).replace(",", "")
        try:
            val = float(raw)
            if 1.0 <= val <= 99999.0:
                candidates.append(val)
        except ValueError:
            continue

    return max(candidates) if candidates else None


# ── Public API ────────────────────────────────────────────────────────

async def ocr_slip_image(image_bytes: bytes) -> dict:
    """
    Run Tesseract (English only) on a slip image.
    Returns {"amount": float_or_none, "raw_text": str, "debug_lines": list}.
    """
    if not TESSERACT_AVAILABLE:
        err = _SETUP_ERROR if "_SETUP_ERROR" in dir() else "Tesseract not installed"
        return {"amount": None, "raw_text": f"[Setup error] {err}", "debug_lines": [f"[Setup error] {err}"]}

    if not image_bytes:
        return {"amount": None, "raw_text": "No image", "debug_lines": []}

    try:
        img = _preprocess(image_bytes)
        raw_text = ""

        # Try two PSM modes — use whichever detects the amount
        for psm in (6, 4, 11):
            cfg = f"--psm {psm} --oem 3 -l eng"
            text = pytesseract.image_to_string(img, config=cfg)
            print(f"[OCR PSM={psm}]\n{text}\n{'─'*40}")
            raw_text = text
            amount = _extract_amount(text)
            if amount:
                return {
                    "amount": amount,
                    "raw_text": text,
                    "debug_lines": text.splitlines(),
                }

        return {
            "amount": None,
            "raw_text": raw_text,
            "debug_lines": raw_text.splitlines(),
        }

    except Exception as e:
        print(f"[OCR Error] {e}")
        return {"amount": None, "raw_text": f"[OCR Error] {e}", "debug_lines": [f"[OCR Error] {e}"]}


def get_status() -> dict:
    """Return Tesseract availability info — used by /ocr-status endpoint."""
    if TESSERACT_AVAILABLE:
        return {
            "available": True,
            "path": pytesseract.pytesseract.tesseract_cmd,
            "version": str(pytesseract.get_tesseract_version()),
        }
    return {"available": False, "error": _SETUP_ERROR if "_SETUP_ERROR" in dir() else "unknown"}