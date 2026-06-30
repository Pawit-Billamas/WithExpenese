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


def read_qr(image_bytes: bytes) -> dict:
    """
    Decode the slip QR and try to extract an amount and/or a reference.

    Returns:
      {
        "found": bool,            # a QR was decoded
        "amount": float | None,   # EMVCo tag 54, if present
        "reference": str,         # tag 62/05 ref or raw fallback
        "raw": str,               # raw decoded payload (trimmed)
      }
    """
    text = _decode_qr_text(image_bytes)
    if not text:
        return {"found": False, "amount": None, "reference": "", "raw": ""}

    result = {"found": True, "amount": None, "reference": "", "raw": text[:120]}

    tags = _parse_emvco_tlv(text)

    # EMVCo tag 54 = Transaction Amount
    amt_raw = tags.get("54")
    if amt_raw:
        try:
            val = float(amt_raw)
            if 0 < val <= 9_999_999:
                result["amount"] = val
        except ValueError:
            pass

    # Reference: EMVCo "Additional Data" (62) often nests ref in subtag 05/01.
    add = tags.get("62", "")
    if add:
        sub = _parse_emvco_tlv(add)
        result["reference"] = sub.get("05") or sub.get("01") or ""

    # Fallback: grab a long alphanumeric run that looks like a transaction ref.
    if not result["reference"]:
        m = re.search(r"[A-Za-z0-9]{12,}", text)
        if m:
            result["reference"] = m.group(0)

    return result
