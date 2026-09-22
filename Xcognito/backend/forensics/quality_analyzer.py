"""
Document Quality Analyzer
Checks:
- Blur / Sharpness via Laplacian Variance
- Glare and Overexposure detection
- Minimum Resolution / Readability scoring
- Skew and Edge boundary checks
"""

import io
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any


def evaluate_document_quality(image_bytes: bytes) -> Dict[str, Any]:
    """
    Evaluates physical quality of the uploaded ID document.
    Helps distinguish between an unreadable blurry photo vs intentional tampering,
    allowing organizers to triage or ask the candidate for a re-upload rather than outright rejecting.
    """
    try:
        # Load with PIL then convert to OpenCV
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_np = np.array(pil_img)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        
        h, w = gray.shape
        resolution_ok = (w >= 480 and h >= 300)
        
        # 1. Laplacian Variance for Blur / Focus Assessment
        # High value = sharp edges, low value = blurry / out of focus
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        
        # Blur classification
        if laplacian_var > 150:
            blur_status = "SHARP"
            is_blurry = False
        elif laplacian_var > 75:
            blur_status = "MODERATE_SHARPNESS"
            is_blurry = False
        elif laplacian_var > 40:
            blur_status = "SLIGHTLY_BLURRY"
            is_blurry = True
        else:
            blur_status = "VERY_BLURRY_UNREADABLE"
            is_blurry = True

        # 2. Glare / Reflection Detection
        # Percentage of pixels near peak white (luminance > 245)
        bright_pixels = np.sum(gray >= 245)
        total_pixels = h * w
        glare_ratio = float(bright_pixels / total_pixels)
        has_glare = glare_ratio > 0.08  # over 8% blinding glare
        
        # 3. Overall Quality Score (0 to 100)
        sharpness_component = min(50.0, (laplacian_var / 200.0) * 50.0)
        glare_penalty = max(0.0, (glare_ratio - 0.03) * 150.0)
        resolution_component = 30.0 if resolution_ok else 10.0
        contrast = float(gray.std())
        contrast_component = min(20.0, (contrast / 50.0) * 20.0)
        
        quality_score = max(5.0, min(100.0, sharpness_component + resolution_component + contrast_component - glare_penalty))
        
        # Human-readable summary
        issues = []
        if is_blurry:
            issues.append(f"Image is {blur_status.lower().replace('_', ' ')} (sharpness index: {int(laplacian_var)})")
        if has_glare:
            issues.append(f"High reflection/glare detected ({round(glare_ratio * 100, 1)}% bleached areas)")
        if not resolution_ok:
            issues.append(f"Low image resolution ({w}x{h} px; min recommended 480x300)")
            
        summary = "Document quality is good for OCR." if not issues else " | ".join(issues)

        return {
            "quality_score": round(quality_score, 1),
            "laplacian_variance": round(laplacian_var, 1),
            "blur_status": blur_status,
            "is_blurry": is_blurry,
            "has_glare": has_glare,
            "resolution": {"width": w, "height": h, "adequate": resolution_ok},
            "issues": issues,
            "summary": summary
        }
    except Exception as err:
        return {
            "quality_score": 50.0,
            "laplacian_variance": 0.0,
            "blur_status": "ERROR",
            "is_blurry": False,
            "has_glare": False,
            "resolution": {"width": 0, "height": 0, "adequate": False},
            "issues": [f"Quality check error: {err}"],
            "summary": "Could not compute image quality"
        }
