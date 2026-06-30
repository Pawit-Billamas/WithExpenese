"""
Free, local, token-less OCR for Thai bank transfer slips (Tesseract).

Reads the *transfer amount* from slip photos (MyMo / KBank / PromptPay style).
No paid API and no API tokens are used — everything runs through Tesseract.

Strategy (robust, Thai-aware):
  1. Preprocess the image (upscale + contrast) in several variants to beat watermarks.
  2. OCR with Thai+English ("tha+eng"); automatically fall back to "eng" if the
     Thai language pack is missing, so it never crashes.
  3. Extract the amount with keyword-anchored passes, explicitly excluding the
     fee line (ค่าธรรมเนียม / fee), which is always 0.00:
        Pass 1: label "จำนวนเงิน"/"จำนวน" alone  -> number on the next line(s)
        Pass 2: label + number on the same line
        Pass 3: number followed by "บาท"
        Pass 4: largest plausible decimal as a fallback
"""
import re
import io
import shutil

try:
    from PIL import Image, ImageEnhance, ImageFilter
    import pytesseract

    # Find tesseract binary:
    #   - Render/Linux installs it at /usr/bin/tesseract
    #   - Windows default install path is used as a fallback
    _tess = (
        shutil.which("tesseract")
        or r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        or "/usr/bin/tesseract"
    )
    pytesseract.pytesseract.tesseract_cmd = _tess

    _version = pytesseract.get_tesseract_version()

    # Detect installed languages so we can choose tha+eng vs eng safely
    try:
        _LANGS = set(pytesseract.get_languages(config=""))
    except Exception:
        _LANGS = set()
    OCR_LANG = "tha+eng" if "tha" in _LANGS else "eng"

    TESSERACT_AVAILABLE = True
    print(f"[OCR] Tesseract {_version} ready at: {_tess} | lang={OCR_LANG}")

except Exception as _e:
    TESSERACT_AVAILABLE = False
    OCR_LANG = "eng"
    _SETUP_ERROR = str(_e)
    print(f"[OCR] Tesseract NOT available: {_e}")


# ── Image preprocessing ───────────────────────────────────────────────

def _preprocess_variants(image_bytes: bytes):
    """
    Return preprocessed PIL images to try, from gentle to aggressive.
    Different slips respond better to different thresholds, so we try several
    and use the first that yields a valid amount.
    """
    base = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    w, h = base.size
    scale = 2 if max(w, h) < 2000 else 1
    if scale != 1:
        base = base.resize((w * scale, h * scale), Image.LANCZOS)

    gray = base.convert("L")
    variants = []

    # Variant A: gentle — keeps thin Thai glyphs
    a = ImageEnhance.Contrast(gray).enhance(1.8).filter(ImageFilter.SHARPEN)
    variants.append(a)

    # Variant B: medium threshold (clean slips)
    b = ImageEnhance.Contrast(gray).enhance(2.5)
    b = b.point(lambda p: 0 if p < 140 else 255)
    variants.append(b)

    # Variant C: aggressive threshold (heavy watermarks)
    c = ImageEnhance.Contrast(gray).enhance(3.5)
    c = ImageEnhance.Brightness(c).enhance(1.15)
    c = c.point(lambda p: 0 if p < 165 else 255).filter(ImageFilter.SHARPEN)
    variants.append(c)

    return variants



# ── Amount extraction (Thai-aware, fee-excluding) ────────────────────

_AMOUNT_LABEL = re.compile(r"จำนวน(?:เงิน)?", re.IGNORECASE)
_FEE_KEYWORDS = ("ค่าธรรมเนียม", "ธรรมเนียม", "fee", "charge")
_NUMBER = re.compile(r"\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?")


def _parse_number(raw: str):
    try:
        val = float(raw.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None
    return val if 1.0 <= val <= 9_999_999.0 else None


def _first_number(line: str, fee_amounts):
    """Return the first valid, non-fee number on a line, or None."""
    for m in _NUMBER.finditer(line):
        raw = m.group().replace(",", "")
        if raw in fee_amounts:
            continue
        val = _parse_number(raw)
        if val is not None:
            return val
    return None


def _has_real_number(line: str, fee_amounts) -> bool:
    return _first_number(line, fee_amounts) is not None


def _find_fee_amounts(lines):
    """Collect numbers that appear on/near a fee line so we can exclude them."""
    fee_amounts = set()
    for i, line in enumerate(lines):
        low = line.lower()
        if any(k in low for k in _FEE_KEYWORDS):
            window = line + " " + (lines[i + 1] if i + 1 < len(lines) else "")
            for m in _NUMBER.finditer(window):
                fee_amounts.add(m.group().replace(",", ""))
    return fee_amounts


def _extract_amount(text: str):
    """Find the transfer amount from raw OCR text. Returns float or None."""
    lines = [ln.strip() for ln in text.splitlines()]
    fee_amounts = _find_fee_amounts(lines)

    # Pass 1: amount label alone on a line -> grab number from next line(s)
    for i, line in enumerate(lines):
        match = _AMOUNT_LABEL.search(line)
        if match and not _has_real_number(line, fee_amounts):
            for j in range(i + 1, min(i + 3, len(lines))):
                val = _first_number(lines[j], fee_amounts)
                if val is not None:
                    return val

    # Pass 2: amount label + number on the same line (take number after label)
    for line in lines:
        match = _AMOUNT_LABEL.search(line)
        if match:
            val = _first_number(line[match.end():], fee_amounts)
            if val is not None:
                return val

    # Pass 3: number immediately followed by บาท
    for m in re.finditer(r"([\d,]+(?:\.\d{1,2})?)\s*บาท", text):
        raw = m.group(1).replace(",", "")
        if raw not in fee_amounts:
            val = _parse_number(raw)
            if val is not None:
                return val

    # Pass 4: largest plausible number as a fallback (prefer X.XX decimals)
    decimals, integers = [], []
    for m in re.finditer(r"\b(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b", text):
        raw = m.group(1).replace(",", "")
        if raw in fee_amounts:
            continue
        val = _parse_number(raw)
        if val is None:
            continue
        (decimals if "." in raw else integers).append(val)
    if decimals:
        return max(decimals)
    if integers:
        return max(integers)
    return None


# ── Core OCR runner (sync) ────────────────────────────────────────────

def _run_ocr(image_bytes: bytes) -> dict:
    if not TESSERACT_AVAILABLE:
        err = _SETUP_ERROR if "_SETUP_ERROR" in dir() else "Tesseract not installed"
        return {"amount": None, "raw_text": f"[Setup error] {err}",
                "debug_lines": [f"[Setup error] {err}"]}

    if not image_bytes:
        return {"amount": None, "raw_text": "No image", "debug_lines": []}

    try:
        variants = _preprocess_variants(image_bytes)
        last_text = ""

        for img in variants:
            for psm in (6, 4, 11):
                cfg = f"--psm {psm} --oem 3 -l {OCR_LANG}"
                text = pytesseract.image_to_string(img, config=cfg)
                last_text = text or last_text
                amount = _extract_amount(text)
                if amount is not None:
                    return {"amount": amount, "raw_text": text,
                            "debug_lines": text.splitlines()}

        return {"amount": None, "raw_text": last_text,
                "debug_lines": last_text.splitlines()}

    except Exception as e:
        print(f"[OCR Error] {e}")
        return {"amount": None, "raw_text": f"[OCR Error] {e}",
                "debug_lines": [f"[OCR Error] {e}"]}


# ── Public API ────────────────────────────────────────────────────────

def ocr_slip_image_sync(image_bytes: bytes) -> dict:
    """
    Synchronous OCR on a slip image (free, no tokens).
    Tesseract is blocking CPU work, so this is sync and safe to call from
    inside the (already-running) FastAPI/uvicorn event loop without spinning
    up a nested loop.
    Returns {"amount": float_or_none, "raw_text": str, "debug_lines": list}.
    """
    return _run_ocr(image_bytes)


async def ocr_slip_image(image_bytes: bytes) -> dict:
    """Async wrapper kept for backward compatibility."""
    return _run_ocr(image_bytes)


def get_status() -> dict:
    """Return Tesseract availability info — used by /ocr-status endpoint."""
    if TESSERACT_AVAILABLE:
        return {
            "available": True,
            "path": pytesseract.pytesseract.tesseract_cmd,
            "version": str(pytesseract.get_tesseract_version()),
            "lang": OCR_LANG,
        }
    return {"available": False,
            "error": _SETUP_ERROR if "_SETUP_ERROR" in dir() else "unknown"}
