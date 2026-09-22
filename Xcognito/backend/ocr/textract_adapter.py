"""
AWS Textract Adapter & OCR Pipeline
Extends Hackingly's existing Textract DOB extraction pipeline into a full document intelligence engine.
Seamlessly falls back to local AI OCR when AWS credentials are not set.
"""

import os
import io
import re
import logging
import threading
from typing import Dict, Any, List, Optional
from PIL import Image
import numpy as np

logger = logging.getLogger("textract_adapter")

# Check if AWS credentials exist
HAS_AWS_CREDENTIALS = bool(
    os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY")
)

# Optional boto3 import
try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    from botocore.config import Config
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


def call_aws_textract(image_bytes: bytes) -> Dict[str, Any]:
    """
    Calls live AWS Textract detect_document_text API with strict timeout configuration.
    """
    if not BOTO3_AVAILABLE:
        raise RuntimeError("boto3 library is not available")

    boto_config = Config(
        connect_timeout=3,
        read_timeout=10,
        retries={"max_attempts": 2, "mode": "standard"}
    )
    client = boto3.client(
        "textract",
        region_name=os.environ.get("AWS_REGION", "ap-south-1"),
        config=boto_config
    )
    response = client.detect_document_text(Document={"Bytes": image_bytes})
    return response


# Thread-safe singleton for EasyOCR reader
_EASYOCR_READER = None
_reader_lock = threading.Lock()

def get_easyocr_reader():
    """Thread-safe singleton for EasyOCR reader to avoid re-instantiating weights per request."""
    global _EASYOCR_READER
    if _EASYOCR_READER is None:
        with _reader_lock:
            if _EASYOCR_READER is None:
                try:
                    import easyocr
                    logger.info("Initializing global EasyOCR model weights...")
                    _EASYOCR_READER = easyocr.Reader(['en'], gpu=False, verbose=False)
                except Exception as e:
                    logger.warning(f"EasyOCR initialization failed: {e}")
                    _EASYOCR_READER = False
    return _EASYOCR_READER if _EASYOCR_READER is not False else None


def local_ocr_fallback(image_bytes: bytes) -> Dict[str, Any]:
    """
    Local AI OCR fallback that mirrors the AWS Textract response schema.
    Uses easyocr or pytesseract if available, with robust image preprocessing.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        logger.error(f"Failed to decode image bytes for OCR: {e}")
        return {"Blocks": [], "DocumentMetadata": {"Pages": 1}, "Source": "Decode Error"}

    img_np = np.array(image)
    width, height = image.size

    raw_lines = []

    # 1. Try EasyOCR first if available
    try:
        reader = get_easyocr_reader()
        if reader:
            results = reader.readtext(img_np)
            blocks = []
            for bbox, text, confidence in results:
                text = text.strip()
                if not text:
                    continue
                raw_lines.append(text)

                # Convert bbox coordinates to Textract normalized bounding box (0.0 to 1.0)
                xs = [pt[0] for pt in bbox]
                ys = [pt[1] for pt in bbox]
                min_x, max_x = max(0, min(xs)), min(width, max(xs))
                min_y, max_y = max(0, min(ys)), min(height, max(ys))

                blocks.append({
                    "BlockType": "LINE",
                    "Text": text,
                    "Confidence": float(confidence * 100),
                    "Geometry": {
                        "BoundingBox": {
                            "Left": float(min_x / width),
                            "Top": float(min_y / height),
                            "Width": float((max_x - min_x) / width),
                            "Height": float((max_y - min_y) / height),
                        }
                    }
                })

            if blocks:
                return {
                    "Blocks": blocks,
                    "DocumentMetadata": {"Pages": 1},
                    "Source": "EasyOCR (Local AI Fallback)"
                }
    except Exception as e:
        logger.info(f"EasyOCR fallback skipped or unavailable: {e}")

    # 2. Try PyTesseract fallback
    try:
        import pytesseract
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        blocks = []
        n_boxes = len(data['level'])

        for i in range(n_boxes):
            text = data['text'][i].strip()
            conf = float(data['conf'][i])
            if text and conf > 20:
                l = data['left'][i]
                t = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                blocks.append({
                    "BlockType": "LINE",
                    "Text": text,
                    "Confidence": conf,
                    "Geometry": {
                        "BoundingBox": {
                            "Left": float(l / width),
                            "Top": float(t / height),
                            "Width": float(w / width),
                            "Height": float(h / height),
                        }
                    }
                })
                raw_lines.append(text)

        if blocks:
            return {
                "Blocks": blocks,
                "DocumentMetadata": {"Pages": 1},
                "Source": "PyTesseract (Local AI Fallback)"
            }
    except Exception as e:
        logger.info(f"PyTesseract fallback skipped or unavailable: {e}")

    # Fallback to structural empty blocks if neither OCR engine detected text
    return {
        "Blocks": [],
        "DocumentMetadata": {"Pages": 1},
        "Source": "Empty / Unprocessed"
    }


def extract_document_ocr(image_bytes: bytes) -> Dict[str, Any]:
    """
    Master OCR extraction pipeline:
    Tries AWS Textract if credentials are present, otherwise automatically falls back to Local AI OCR.
    """
    if HAS_AWS_CREDENTIALS and BOTO3_AVAILABLE:
        try:
            res = call_aws_textract(image_bytes)
            res["Source"] = "AWS Textract (Cloud)"
            return res
        except Exception as err:
            logger.warning(f"AWS Textract call failed, falling back to local OCR: {err}")

    return local_ocr_fallback(image_bytes)


# --- Backward Compatible Interface for Hackingly's Existing DOB Pipeline ---
def extract_dob_legacy_textract(image_bytes: bytes) -> Dict[str, Any]:
    """
    Direct drop-in replacement for Hackingly's existing DOB extraction pipeline.
    Preserves exact contract: extracts Date of Birth string and computed age.
    """
    ocr_result = extract_document_ocr(image_bytes)
    blocks = ocr_result.get("Blocks", [])

    dob_pattern = r"(?:DOB|Date of Birth|D\.O\.B|Birth Date|Year of Birth)[:\s]*([0-9]{2}[/\-\.][0-9]{2}[/\-\.][0-9]{4}|[0-9]{4})"

    extracted_dob = None
    extracted_age = None
    confidence = 0.0

    current_year = 2026

    for block in blocks:
        if block.get("BlockType") == "LINE":
            text = block.get("Text", "")
            match = re.search(dob_pattern, text, re.IGNORECASE)
            if match:
                extracted_dob = match.group(1)
                confidence = block.get("Confidence", 90.0)

                # Parse age
                try:
                    if len(extracted_dob) == 4:
                        birth_year = int(extracted_dob)
                    else:
                        sep = "/" if "/" in extracted_dob else ("-" if "-" in extracted_dob else ".")
                        parts = extracted_dob.split(sep)
                        birth_year = int(parts[2])
                    extracted_age = current_year - birth_year
                except Exception:
                    pass
                break

    return {
        "dob": extracted_dob,
        "age": extracted_age,
        "confidence": confidence,
        "source": ocr_result.get("Source", "Unknown")
    }
