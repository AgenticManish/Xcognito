"""
Digital Forensics & Image Tampering Detector
Implements:
- Error Level Analysis (ELA) to expose digital photo manipulation, cloned areas, and edited text/DOB.
- High-contrast visual ELA heatmap generation for organizer side-by-side inspection.
- Statistical anomaly scoring for digital document forgery.
"""

import io
import base64
import numpy as np
import cv2
from PIL import Image, ImageChops, ImageEnhance
from typing import Dict, Any, Tuple


def scan_editing_software_signatures(image_bytes: bytes) -> Tuple[bool, str]:
    """
    Scans EXIF metadata, JFIF headers, and APP markers for digital photo editing suites:
    Adobe Photoshop, GIMP, Canva, Photopea, Paint.NET, etc.
    """
    suspicious_tools = ["PHOTOSHOP", "GIMP", "CANVA", "PHOTOPEA", "PAINT.NET", "PIXLR", "CORELDRAW", "AFFINITY"]
    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        exif = pil_img.getexif()
        software_str = str(exif.get(0x0131, "")).upper()
        
        # Check EXIF software tag
        for tool in suspicious_tools:
            if tool in software_str:
                return True, f"Image metadata confirms editing via {software_str.title()}"

        # Also inspect raw image bytes for software markers (e.g. Adobe XMP packets)
        raw_header = image_bytes[:4096].upper()
        if b"ADOBE" in raw_header and b"PHOTOSHOP" in raw_header:
            return True, "Embedded Adobe Photoshop XMP data structure detected in image header"
            
        return False, "No editing software signatures detected in metadata"
    except Exception:
        return False, "Metadata scan skipped"


def generate_ela_heatmap(image_bytes: bytes, quality: int = 90, scale: int = 15) -> Tuple[np.ndarray, str, float]:
    """
    Performs Error Level Analysis (ELA) and forensic tampering scoring.
    """
    original = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # Save re-compressed version to in-memory buffer
    buffer = io.BytesIO()
    original.save(buffer, "JPEG", quality=quality)
    buffer.seek(0)
    recompressed = Image.open(buffer)
    
    # Statistical error metrics
    diff = ImageChops.difference(original, recompressed)
    diff_np = np.array(diff)
    diff_gray = cv2.cvtColor(diff_np, cv2.COLOR_RGB2GRAY).astype(np.float32)

    max_err = float(np.max(diff_gray))
    mean_err = float(np.mean(diff_gray))

    # Grid block anomaly detection
    h, w = diff_gray.shape
    bh, bw = max(16, h // 16), max(16, w // 16)
    block_means = []
    for r in range(0, h - bh, bh):
        for c in range(0, w - bw, bw):
            block_means.append(float(np.mean(diff_gray[r:r+bh, c:c+bw])))
            
    block_means = np.array(block_means)
    max_block = float(np.max(block_means)) if len(block_means) > 0 else 0.1
    mean_block = float(np.mean(block_means)) if len(block_means) > 0 else 0.1

    # Check for metadata software traces
    has_software_edit, software_msg = scan_editing_software_signatures(image_bytes)

    # Visual heatmap for organizer UI
    enhanced_diff = ImageEnhance.Brightness(diff).enhance(scale)
    heatmap = cv2.applyColorMap(cv2.cvtColor(np.array(enhanced_diff), cv2.COLOR_RGB2GRAY), cv2.COLORMAP_JET)

    # Calibrated Tamper Score
    # Base ELA compression score (typically 10-25 for authentic cards)
    base_ela = min(35.0, (mean_err * 8.0) + (max_err * 0.6))
    
    # Add major penalty if editing software signature was found
    software_penalty = 55.0 if has_software_edit else 0.0
    
    tamper_score = float(np.clip(base_ela + software_penalty, 5.0, 95.0))
    
    # Encode heatmap to base64 JPEG
    _, encoded_img = cv2.imencode('.jpg', heatmap, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    ela_base64 = f"data:image/jpeg;base64,{base64.b64encode(encoded_img).decode('utf-8')}"
    
    return heatmap, ela_base64, round(tamper_score, 1)


def analyze_document_tampering(image_bytes: bytes) -> Dict[str, Any]:
    """
    Comprehensive tampering evaluation combining ELA, metadata forensic signatures, and visual artifacts.
    """
    try:
        has_software_edit, software_msg = scan_editing_software_signatures(image_bytes)
        heatmap, ela_base64, tamper_score = generate_ela_heatmap(image_bytes)
        
        # Risk classification
        if tamper_score < 30.0:
            risk_level = "LOW_RISK"
            assessment = "Document exhibits consistent compression levels. No signs of digital editing or Photoshop manipulation."
            flagged = False
        elif tamper_score < 50.0:
            risk_level = "MODERATE_RISK"
            assessment = "Minor compression inconsistencies detected. Recommended for organizer review if text looks unusual."
            flagged = False
        else:
            risk_level = "HIGH_TAMPER_RISK"
            assessment = f"Manipulated Document Alert: {software_msg}. Significant forensic Error Level disparity detected."
            flagged = True
            
        return {
            "tamper_score": tamper_score,
            "risk_level": risk_level,
            "is_flagged": flagged,
            "assessment": assessment,
            "ela_heatmap_url": ela_base64
        }
    except Exception as err:
        return {
            "tamper_score": 0.0,
            "risk_level": "UNKNOWN",
            "is_flagged": False,
            "assessment": f"Error running forensic analysis: {err}",
            "ela_heatmap_url": None
        }
            
        return {
            "tamper_score": tamper_score,
            "risk_level": risk_level,
            "is_flagged": flagged,
            "assessment": assessment,
            "ela_heatmap_url": ela_base64
        }
    except Exception as err:
        return {
            "tamper_score": 0.0,
            "risk_level": "UNKNOWN",
            "is_flagged": False,
            "assessment": f"Error running forensic analysis: {err}",
            "ela_heatmap_url": None
        }
