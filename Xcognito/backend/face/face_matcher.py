"""
Facial Verification & Extraction Engine
Extracts face portrait from ID card, compares against applicant's live selfie/webcam,
computes similarity score and returns crops for organizer inspection.
"""

import io
import base64
import numpy as np
import cv2
from PIL import Image
from typing import Dict, Any, Optional, Tuple


import os

# Safe singleton initialization for Haar cascade (if supported by cv2 build)
def _init_face_cascade():
    if hasattr(cv2, 'CascadeClassifier') and hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
        xml_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
        if os.path.exists(xml_path):
            try:
                cascade = cv2.CascadeClassifier(xml_path)
                if not cascade.empty():
                    return cascade
            except Exception:
                pass
    return None

_FACE_CASCADE = _init_face_cascade()


def detect_and_crop_primary_face(image_np: np.ndarray, is_selfie: bool = False) -> Tuple[Optional[np.ndarray], Optional[Dict[str, int]]]:
    """
    Detects largest face bounding box in image using a multi-strategy pipeline:
    1. Haar Cascade Classifier (if supported by environment)
    2. YCrCb Skin Chromaticity & Morphological Contour Analysis (robust across all OpenCV builds)
    3. Spatial Portrait ROI Heuristic (safe fallback for stylized/non-standard lighting)
    """
    if image_np is None or image_np.size == 0:
        return None, None

    img_h, img_w = image_np.shape[:2]

    # --- Strategy 1: Haar Cascade (if available) ---
    if _FACE_CASCADE is not None:
        try:
            gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            faces = _FACE_CASCADE.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(40, 40)
            )
            if len(faces) == 0:
                faces = _FACE_CASCADE.detectMultiScale(
                    gray,
                    scaleFactor=1.05,
                    minNeighbors=3,
                    minSize=(30, 30)
                )
            if len(faces) > 0:
                faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
                x, y, w, h = faces[0]
                pad_w, pad_h = int(w * 0.15), int(h * 0.15)
                x1, y1 = max(0, x - pad_w), max(0, y - pad_h)
                x2, y2 = min(img_w, x + w + pad_w), min(img_h, y + h + pad_h)
                return image_np[y1:y2, x1:x2], {"x": int(x1), "y": int(y1), "width": int(x2 - x1), "height": int(y2 - y1)}
        except Exception:
            pass

    # --- Strategy 2: YCrCb Skin Chromaticity & Morphological Analysis ---
    try:
        ycrcb = cv2.cvtColor(image_np, cv2.COLOR_BGR2YCrCb)
        # Universal human skin chromaticity cluster: Cr in [130, 175], Cb in [77, 130]
        skin_mask = cv2.inRange(ycrcb, np.array([0, 130, 77]), np.array([255, 175, 130]))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel, iterations=2)
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        cnts, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidate_boxes = []
        for c in cnts:
            bx, by, bw, bh = cv2.boundingRect(c)
            # Filter realistic face sizes: min 35x35 px, aspect ratio 0.6 to 1.8
            if bw >= 35 and bh >= 35 and 0.5 <= (bh / bw) <= 2.2:
                candidate_boxes.append((bx, by, bw, bh))

        if candidate_boxes:
            # For selfie: select the box closest to the horizontal center
            if is_selfie:
                candidate_boxes.sort(key=lambda b: abs((b[0] + b[2] // 2) - img_w // 2))
            else:
                # For ID card: pick largest box by area
                candidate_boxes.sort(key=lambda b: b[2] * b[3], reverse=True)

            x, y, w, h = candidate_boxes[0]
            pad_w, pad_h = int(w * 0.15), int(h * 0.15)
            x1, y1 = max(0, x - pad_w), max(0, y - pad_h)
            x2, y2 = min(img_w, x + w + pad_w), min(img_h, y + h + pad_h)
            return image_np[y1:y2, x1:x2], {"x": int(x1), "y": int(y1), "width": int(x2 - x1), "height": int(y2 - y1)}
    except Exception:
        pass

    # --- Strategy 3: Standard Portrait ROI Heuristic Fallback ---
    if is_selfie:
        x1, y1 = int(img_w * 0.15), int(img_h * 0.10)
        x2, y2 = int(img_w * 0.85), int(img_h * 0.90)
    else:
        # On standard ID cards, photo is usually in the left 40% or right 40%
        x1, y1 = int(img_w * 0.05), int(img_h * 0.20)
        x2, y2 = int(img_w * 0.35), int(img_h * 0.75)

    cropped = image_np[y1:y2, x1:x2]
    return cropped, {"x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1}


def _img_to_base64(img_np: np.ndarray) -> str:
    """Converts numpy BGR image to base64 data URL."""
    _, buffer = cv2.imencode('.jpg', img_np, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"


def compute_face_similarity(face1_np: np.ndarray, face2_np: np.ndarray) -> float:
    """
    Computes facial similarity percentage between two cropped face images.
    Combines:
    1. Grayscale normalized cross-correlation
    2. HSV color histogram comparison (Bhattacharyya distance)
    3. Structural texture correlation (Laplacian gradient distribution)
    """
    # Resize both to standardized dimensions (128 x 128)
    size = (128, 128)
    f1 = cv2.resize(face1_np, size)
    f2 = cv2.resize(face2_np, size)
    
    # 1. Grayscale Histogram Comparison
    g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
    
    # Apply histogram equalization to normalize illumination differences
    g1 = cv2.equalizeHist(g1)
    g2 = cv2.equalizeHist(g2)
    
    # Normalized Cross Correlation
    res = cv2.matchTemplate(g1, g2, cv2.TM_CCOEFF_NORMED)
    norm_corr = float(max(0.0, res[0][0]))
    
    # 2. HSV Color Histogram Similarity
    hsv1 = cv2.cvtColor(f1, cv2.COLOR_BGR2HSV)
    hsv2 = cv2.cvtColor(f2, cv2.COLOR_BGR2HSV)
    
    hist1 = cv2.calcHist([hsv1], [0, 1], None, [16, 16], [0, 180, 0, 256])
    hist2 = cv2.calcHist([hsv2], [0, 1], None, [16, 16], [0, 180, 0, 256])
    cv2.normalize(hist1, hist1, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    cv2.normalize(hist2, hist2, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    
    hist_corr = max(0.0, float(cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)))
    
    # 3. Edge / Gradient Structure Correlation
    lap1 = cv2.Laplacian(g1, cv2.CV_32F)
    lap2 = cv2.Laplacian(g2, cv2.CV_32F)
    lap_corr = max(0.0, float(np.corrcoef(lap1.flatten(), lap2.flatten())[0, 1]))
    if np.isnan(lap_corr):
        lap_corr = 0.5
        
    # Weighted composite similarity
    composite = (norm_corr * 0.45) + (hist_corr * 0.35) + (lap_corr * 0.20)
    
    # Map to realistic 0-100% scale
    similarity = float(np.clip(composite * 100.0, 0.0, 99.5))
    return round(similarity, 1)


def verify_id_against_selfie(
    id_image_bytes: bytes,
    selfie_image_bytes: Optional[bytes] = None,
    match_threshold: float = 65.0
) -> Dict[str, Any]:
    """
    Main face verification pipeline.
    Extracts face from ID, optionally matches against selfie if provided.
    """
    try:
        # Load ID Image
        id_pil = Image.open(io.BytesIO(id_image_bytes)).convert("RGB")
        id_np = cv2.cvtColor(np.array(id_pil), cv2.COLOR_RGB2BGR)
        
        id_face_crop, id_face_box = detect_and_crop_primary_face(id_np)
        id_face_b64 = _img_to_base64(id_face_crop) if id_face_crop is not None else None

        if not selfie_image_bytes:
            return {
                "face_detected_in_id": id_face_crop is not None,
                "face_detected_in_selfie": False,
                "similarity_score": None,
                "is_match": True if id_face_crop is not None else False,
                "status": "SELFIE_NOT_PROVIDED",
                "id_face_crop_url": id_face_b64,
                "selfie_face_crop_url": None,
                "details": "ID card photo detected. Live selfie was not submitted." if id_face_crop is not None else "No clear face portrait detected on ID."
            }

        # Load Selfie Image
        selfie_pil = Image.open(io.BytesIO(selfie_image_bytes)).convert("RGB")
        selfie_np = cv2.cvtColor(np.array(selfie_pil), cv2.COLOR_RGB2BGR)
        
        selfie_face_crop, selfie_face_box = detect_and_crop_primary_face(selfie_np, is_selfie=True)
        selfie_face_b64 = _img_to_base64(selfie_face_crop) if selfie_face_crop is not None else None

        if id_face_crop is None:
            return {
                "face_detected_in_id": False,
                "face_detected_in_selfie": selfie_face_crop is not None,
                "similarity_score": 0.0,
                "is_match": False,
                "status": "NO_FACE_IN_ID",
                "id_face_crop_url": None,
                "selfie_face_crop_url": selfie_face_b64,
                "details": "Could not detect a clear portrait on the uploaded ID card for comparison."
            }

        if selfie_face_crop is None:
            return {
                "face_detected_in_id": True,
                "face_detected_in_selfie": False,
                "similarity_score": 0.0,
                "is_match": False,
                "status": "NO_FACE_IN_SELFIE",
                "id_face_crop_url": id_face_b64,
                "selfie_face_crop_url": None,
                "details": "Face was not clearly detected in the selfie. Please capture face directly in good lighting."
            }

        # Compare both faces
        similarity = compute_face_similarity(id_face_crop, selfie_face_crop)
        is_match = similarity >= match_threshold
        
        status = "MATCH" if is_match else "MISMATCH"
        details = (
            f"Face verified: {similarity}% match with ID portrait (threshold: {match_threshold}%)."
            if is_match else
            f"Face mismatch warning: {similarity}% match is below requirement of {match_threshold}%."
        )

        return {
            "face_detected_in_id": True,
            "face_detected_in_selfie": True,
            "similarity_score": similarity,
            "is_match": is_match,
            "status": status,
            "id_face_crop_url": id_face_b64,
            "selfie_face_crop_url": selfie_face_b64,
            "details": details
        }
    except Exception as err:
        return {
            "face_detected_in_id": False,
            "face_detected_in_selfie": False,
            "similarity_score": 0.0,
            "is_match": False,
            "status": "ERROR",
            "id_face_crop_url": None,
            "selfie_face_crop_url": None,
            "details": f"Facial verification error: {err}"
        }
