"""
FREE OCR Service using Tesseract
Reads Thai payment slip images and extracts transaction amounts
"""
import re
import io
from datetime import datetime
from PIL import Image
import cv2
import numpy as np

try:
    import pytesseract
    # Set Tesseract path for Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


async def ocr_slip_image(image_bytes: bytes) -> dict:
    """
    OCR payment slip image and extract amount.
    
    Returns a dict with keys:
        - amount (float or None)
        - description (str)
        - date (str)
        - raw_text (str)
    """
    if not TESSERACT_AVAILABLE:
        return {
            "amount": None,
            "description": "Tesseract not installed",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "raw_text": "Please install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki"
        }
    
    try:
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to OpenCV format for preprocessing
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Preprocess image for better OCR
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding to get better contrast
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        # OCR with Thai language support
        try:
            text = pytesseract.image_to_string(thresh, lang='tha+eng')
        except:
            # Fallback to English only
            text = pytesseract.image_to_string(thresh, lang='eng')
        
        # Extract amount from text
        amount = extract_amount_from_text(text)
        
        # Try to extract date
        date_str = extract_date_from_text(text)
        
        return {
            "amount": amount,
            "description": "Payment slip",
            "date": date_str or datetime.now().strftime("%Y-%m-%d"),
            "raw_text": text
        }
    
    except Exception as e:
        return {
            "amount": None,
            "description": f"OCR Error: {str(e)}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "raw_text": f"Error processing image: {str(e)}"
        }


def extract_amount_from_text(text: str) -> float | None:
    """
    Extract amount from OCR text.
    Looks for common patterns in Thai payment slips.
    """
    # Remove commas and spaces
    text = text.replace(',', '').replace(' ', '')
    
    # Common patterns for amounts in Thai slips
    patterns = [
        r'จำนวนเงิน[:\s]*(\d+\.?\d*)',  # "จำนวนเงิน: 140.00"
        r'(\d{2,}\.\d{2})(?:บาท|THB)',   # "140.00 บาท"
        r'(?:^|\n)(\d{2,}\.\d{2})(?:\n|$)',  # Standalone number with decimals
        r'(?:Total|Amount)[:\s]*(\d+\.?\d*)',  # English format
        r'(\d{3,}\.?\d*)',  # Any 3+ digit number
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                amount = float(matches[0])
                # Filter out unrealistic amounts (< 1 or > 1,000,000)
                if 1 <= amount <= 1000000:
                    return amount
            except (ValueError, IndexError):
                continue
    
    return None


def extract_date_from_text(text: str) -> str | None:
    """Extract date from OCR text."""
    # Thai date formats: "26 มิ.ย. 2569", "26/06/2569"
    patterns = [
        r'(\d{1,2})\s*[/.-]\s*(\d{1,2})\s*[/.-]\s*(\d{4})',  # DD/MM/YYYY
        r'(\d{1,2})\s+([ม\.กพมยพยธคสพย]\S*)\s+(\d{4})',  # DD MMM YYYY (Thai)
    ]
    
    for pattern in patterns:
        matches = re.search(pattern, text)
        if matches:
            try:
                day = int(matches.group(1))
                # Convert Buddhist year to Gregorian if needed
                year = int(matches.group(3))
                if year > 2500:  # Buddhist year
                    year -= 543
                return f"{year:04d}-{int(matches.group(2)):02d}-{day:02d}"
            except:
                pass
    
    return None
