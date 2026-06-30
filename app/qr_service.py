"""
QR fallback for slip reading — free, no tokens, no system binary.

Thai bank slips embed a QR code. Two useful things can come out of it:
  1. An EMVCo TLV payload that *sometimes* contains the transaction amount
     (tag "54"). When present, we use it directly — very accurate.
  2. A slip-verification reference (sending bank + transaction ref). The amount
     is usually NOT in the QR for KBank/MyMo verify QRs, so we surface the
     reference so the user can confirm the amount instead of guessing.

Decoding uses OpenCV's built-in QRCodeDetector (pip: opencv-python-headless),
so there is no external binary and nothing to pay for.
"""
import io
import re

try:
    import cv2
    import numpy as np
    from PIL import Image

    QR_AVAILABLE = True
    _QR_SETUP_ERROR = ""
except Exception as _e:  # pragma: no cover
    QR_AVAILABLE = False
    _QR_SETUP_ERROR = f"{type(_e).__name__}: {_e}"
    print(f"[QR] OpenCV not available: {_QR_SETUP_ERROR}")


def _decode_qr_text(image_bytes: bytes) -> str:
    """Return the raw decoded QR string, or '' if none/undecodable."""
    if not QR_AVAILABLE or not image_bytes:
        return ""
    try:
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        arr = np.array(pil)[:, :, ::-1]  # RGB -> BGR for OpenCV
        detector = cv2.QRCodeDetector()

        # Try direct decode first
        data, _pts, _ = detector.detectAndDecode(arr)
        if data:
            return data

        # Retry on an upscaled, grayscale image (small/blurry QRs)
        gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape[:2]
        big = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        data, _pts, _ = detector.detectAndDecode(big)
        return data or ""
    except Exception as e:
        print(f"[QR decode error] {e}")
        return ""


def _parse_emvco_tlv(payload: str) -> dict:
    """
    Parse an EMVCo TLV string (ID + 2-digit length + value).
    Returns a flat dict of top-level tag -> value. Best-effort; tolerant of
    non-EMV payloads (returns {}).
    """
    tags = {}
    i, n = 0, len(payload)
    while i + 4 <= n:
        tag = payload[i:i + 2]
        length_str = payload[i + 2:i + 4]
        if not (tag.isdigit() and length_str.isdigit()):
            break
        length = int(length_str)
        start = i + 4
        end = start + length
        if end > n:
            break
        tags[tag] = payload[start:end]
        i = end
    return tags


def _is_emv_payment_qr(text: str) -> bool:
    """
    True only for a genuine EMVCo merchant-presented QR, which always starts
    with the Payload Format Indicator '000201'. Thai bank *slip-verification*
    QR codes do NOT start with this — they are a different (proprietary) format
    that carries a reference, NOT the amount. We must never read an amount from
    those, otherwise account/ref digits (e.g. 7515) get misread as the amount.
    """
    return text.startswith("000201")


def _amount_from_emv(text: str):
    """
    Extract the transaction amount (EMVCo tag 54) from a *validated* EMV QR.
    Tag 54 is a numeric string like '100.00'. Returns float or None.
    Only top-level tag 54 is trusted (never nested/account/ref digits).
    """
    tags = _parse_emvco_tlv(text)
    amt_raw = tags.get("54")
    if not amt_raw:
        return None
    # Must look like a clean money value: digits with optional one dot + decimals
    if not re.fullmatch(r"\d{1,9}(?:\.\d{1,2})?", amt_raw):
        return None
    try:
        val = float(amt_raw)
    except ValueError:
        return None
    return val if 0 < val <= 9_999_999 else None


def _reference_from_qr(text: str) -> str:
    """Best-effort transaction reference for display only (never an amount)."""
    # EMV "Additional Data" (62) often nests a ref in subtag 05/01.
    tags = _parse_emvco_tlv(text)
    add = tags.get("62", "")
    if add:
        sub = _parse_emvco_tlv(add)
        ref = sub.get("05") or sub.get("01") or ""
        if ref:
            return ref
    # Otherwise the longest alphanumeric run (e.g. KBank '...COR06494').
    runs = re.findall(r"[A-Za-z0-9]{10,}", text)
    return max(runs, key=len) if runs else ""


def read_qr(image_bytes: bytes) -> dict:
    """
    Decode the slip QR.

    IMPORTANT: We only return an `amount` when the QR is a genuine EMVCo
    payment QR (starts with '000201') with a clean tag-54 value. Thai bank
    slip-verification QRs do not contain the amount, so for those we return
    amount=None and only a reference — this prevents misreading account/ref
    digits (the 515 bug) as the paid amount.

    Returns:
      {
        "found": bool,
        "amount": float | None,
        "reference": str,
        "raw": str,
      }
    """
    text = _decode_qr_text(image_bytes)
    if not text:
        return {"found": False, "amount": None, "reference": "", "raw": ""}

    result = {"found": True, "amount": None, "reference": "", "raw": text[:120]}

    if _is_emv_payment_qr(text):
        result["amount"] = _amount_from_emv(text)

    result["reference"] = _reference_from_qr(text)
    return result
