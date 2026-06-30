"""
OCR using Tesseract — optimised for Thai bank transfer slips (MyMo, KBank, etc.)
No API keys or AI needed.
"""
import re
import io

try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


# ── Image preprocessing ───────────────────────────────────────────────

def _preprocess(image_bytes: bytes) -> "Image.Image":
    """
    Scale up 2× then binarise to kill watermarks (mymo pattern, KBank building).
    High contrast + threshold → clean black text on white.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Scale up 2× — Tesseract reads larger text much more reliably
    w, h = img.size
    img = img.resize((w * 2, h * 2), Image.LANCZOS)

    # Grayscale
    img = img.convert("L")

    # Aggressive contrast boost to kill light watermarks
    img = ImageEnhance.Contrast(img).enhance(3.5)
    img = ImageEnhance.Brightness(img).enhance(1.2)

    # Hard binarise: anything below 160 → black, else white
    img = img.point(lambda p: 0 if p < 160 else 255)

    # One pass of sharpening
    img = img.filter(ImageFilter.SHARPEN)

    return img


# ── Amount extraction ─────────────────────────────────────────────────

def _find_fee_amounts(lines: list[str]) -> set[str]:
    """
    Collect numbers that appear on / immediately after a fee label line.
    Only match decimal-formatted amounts (e.g. 0.00) to avoid false positives
    from reference numbers like 6181151438001000015B9790.
    """
    fee_amounts: set[str] = set()
    fee_keywords = ("ค่าธรรมเนียม", "ธรรมเนียม", "fee", "charge")
    for i, line in enumerate(lines):
        low = line.lower()
        if any(k in low for k in fee_keywords):
            check = line + " " + (lines[i + 1] if i + 1 < len(lines) else "")
            # Only grab numbers that have a decimal point (real amounts like 0.00)
            for m in re.finditer(r"\d[\d,]*\.\d{1,2}", check):
                fee_amounts.add(m.group().replace(",", ""))
    return fee_amounts



def _parse_number(raw: str) -> float | None:
    try:
        val = float(raw.replace(",", "").strip())
        return val if 1.0 <= val <= 999999.0 else None
    except ValueError:
        return None


def _extract_amount(text: str) -> float | None:
    """
    Priority order:
    1. Number on the line immediately after จำนวนเงิน / จำนวน  (MyMo & KBank style)
    2. Number on the same line as จำนวน followed by บาท
    3. Any number + บาท that isn't a fee
    4. Fallback: largest non-zero, non-fee number in range 1–99999
    """
    lines = [ln.strip() for ln in text.splitlines()]
    fee_amounts = _find_fee_amounts(lines)

    amount_keywords = re.compile(
        r"^จำนวน(?:เงิน)?\s*[:\s]*$|^จำนวน(?:เงิน)?\s*[:\s]*(\d[\d,\.]*)",
        re.IGNORECASE,
    )

    # ── Pass 1: keyword on its own line → grab number from next line ──
    for i, line in enumerate(lines):
        # Keyword alone on a line (e.g. "จำนวนเงิน" or "จำนวน:")
        if re.match(r"^จำนวน(?:เงิน)?\s*[:\s]*$", line, re.IGNORECASE):
            for j in range(i + 1, min(i + 3, len(lines))):
                # Grab first number in the following line(s)
                m = re.search(r"([\d,]+\.?\d*)", lines[j])
                if m:
                    raw = m.group(1).replace(",", "")
                    if raw not in fee_amounts:
                        val = _parse_number(raw)
                        if val and val > 0:
                            return val

    # ── Pass 2: keyword + number on same line (e.g. "จำนวน: 100.00 บาท") ──
    inline = re.compile(
        r"จำนวน(?:เงิน)?\s*[:\s]+([\d,]+\.?\d*)", re.IGNORECASE
    )
    for m in inline.finditer(text):
        raw = m.group(1).replace(",", "")
        if raw not in fee_amounts:
            val = _parse_number(raw)
            if val and val > 0:
                return val

    # ── Pass 3: any "NUMBER บาท" that isn't a fee ────────────────────
    for m in re.finditer(r"([\d,]+\.?\d*)\s*บาท", text):
        raw = m.group(1).replace(",", "")
        if raw not in fee_amounts:
            val = _parse_number(raw)
            if val and val > 0:
                return val

    # ── Pass 4: fallback — largest plausible non-fee number ──────────
    candidates = []
    for m in re.finditer(r"\b(\d{2,6}(?:\.\d{1,2})?)\b", text):
        raw = m.group(1)
        if raw not in fee_amounts:
            val = _parse_number(raw)
            if val and val > 0:
                candidates.append(val)
    return max(candidates) if candidates else None


# ── Public API ────────────────────────────────────────────────────────

async def ocr_slip_image(image_bytes: bytes) -> dict:
    """
    Run Tesseract on a slip image.
    Returns {"amount": float_or_none, "raw_text": str, "debug_lines": list}.
    """
    if not TESSERACT_AVAILABLE or not image_bytes:
        return {"amount": None, "raw_text": "", "debug_lines": []}

    try:
        img = _preprocess(image_bytes)

        # Try two PSM modes; use whichever finds the amount
        for psm in (6, 4):
            cfg = f"--psm {psm} --oem 3"
            raw_text = pytesseract.image_to_string(img, lang="tha+eng", config=cfg)
            print(f"[OCR PSM={psm}]\n{raw_text}\n{'─'*40}")
            amount = _extract_amount(raw_text)
            if amount:
                return {
                    "amount": amount,
                    "raw_text": raw_text,
                    "debug_lines": raw_text.splitlines(),
                }

        # Neither PSM found an amount — return raw text so bot can show it
        return {"amount": None, "raw_text": raw_text, "debug_lines": raw_text.splitlines()}

    except Exception as e:
        print(f"[OCR Error] {e}")
        return {"amount": None, "raw_text": str(e), "debug_lines": []}