"""
Realistic Anonymized Indian ID Sample Generator & Test Fixtures
Generates valid synthetic Aadhaar, College ID, and PAN cards for testing all key scenarios:
1. Valid Student (Aadhaar + College ID) -> Pass
2. Underage Candidate (DOB 2011) -> Fail Age Check
3. Digitally Tampered DOB (Photoshop simulation) -> High ELA Tamper Alert
4. Duplicate ID (Sybil Attack) -> Multi-registration Fraud
5. Blurry / Glare Photo -> Route to Manual Review
6. Face Mismatch -> Facial likeness warning
"""

import io
import os
import base64
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cv2
from backend.ocr.checksums import compute_verhoeff_checksum

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "sample_cards")
os.makedirs(SAMPLES_DIR, exist_ok=True)


def _draw_synthetic_portrait(draw: ImageDraw.ImageDraw, box: tuple, seed: int = 42):
    """Draws a clean synthetic stylized human face portrait on the ID card."""
    x0, y0, x1, y1 = box
    w = x1 - x0
    h = y1 - y0
    
    # Background
    draw.rectangle([x0, y0, x1, y1], fill=(220, 230, 242), outline=(140, 160, 190), width=2)
    
    # Head/Face
    center_x = x0 + w // 2
    face_w = int(w * 0.5)
    face_h = int(h * 0.55)
    face_y0 = y0 + int(h * 0.2)
    
    # Hair
    draw.ellipse([center_x - int(face_w * 0.65), face_y0 - 8, center_x + int(face_w * 0.65), face_y0 + face_h - 10], fill=(40, 30, 25))
    
    # Skin
    draw.ellipse([center_x - face_w // 2, face_y0, center_x + face_w // 2, face_y0 + face_h], fill=(235, 190, 155))
    
    # Eyes
    eye_y = face_y0 + int(face_h * 0.4)
    draw.ellipse([center_x - 14, eye_y, center_x - 6, eye_y + 6], fill=(30, 30, 30))
    draw.ellipse([center_x + 6, eye_y, center_x + 14, eye_y + 6], fill=(30, 30, 30))
    
    # Smile
    draw.arc([center_x - 12, face_y0 + int(face_h * 0.6), center_x + 12, face_y0 + int(face_h * 0.75)], start=0, end=180, fill=(150, 60, 60), width=2)
    
    # Shoulders / Torso
    draw.ellipse([center_x - int(w * 0.45), y0 + int(h * 0.65), center_x + int(w * 0.45), y1 + 30], fill=(45, 85, 150))


def create_sample_aadhaar(
    name: str = "AARAV SHARMA",
    dob: str = "15/08/2004",
    gender: str = "MALE",
    aadhaar_11_digits: str = "98432109876",
    tamper_dob: bool = False,
    is_blurry: bool = False
) -> bytes:
    """
    Generates a realistic synthetic Aadhaar card image.
    Uses proper Verhoeff check digit for true checksum compliance.
    If tamper_dob is True, splices an edited text block to create a detectable ELA anomaly!
    """
    width, height = 700, 440
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Decorative header bands (Saffron, White, Green)
    draw.rectangle([0, 0, width, 14], fill=(255, 153, 51))
    draw.rectangle([0, 14, width, 24], fill=(255, 255, 255))
    draw.rectangle([0, 24, width, 38], fill=(19, 136, 8))

    # Header Text
    draw.text((220, 48), "GOVERNMENT OF INDIA", fill=(10, 30, 80))
    draw.text((230, 68), "Unique Identification Authority of India", fill=(80, 80, 80))
    draw.line([(30, 95), (width - 30, 95)], fill=(200, 200, 200), width=1)

    # Portrait photo box
    _draw_synthetic_portrait(draw, (45, 120, 185, 300))

    # Details text
    draw.text((220, 130), f"Name: {name}", fill=(20, 20, 20))
    draw.text((220, 165), f"DOB: {dob}", fill=(20, 20, 20))
    draw.text((220, 200), f"Gender: {gender}", fill=(20, 20, 20))
    draw.text((220, 235), "Mera Aadhaar, Meri Pehchan", fill=(120, 120, 120))

    # Compute Verhoeff 12th digit
    check_digit = compute_verhoeff_checksum(aadhaar_11_digits)
    full_12 = f"{aadhaar_11_digits}{check_digit}"
    formatted_aadhaar = f"{full_12[0:4]} {full_12[4:8]} {full_12[8:12]}"

    # Bottom aadhaar number banner
    draw.rectangle([30, 325, width - 30, 375], fill=(245, 247, 250), outline=(220, 225, 235))
    draw.text((240, 340), formatted_aadhaar, fill=(180, 30, 30))

    # Footer
    draw.rectangle([0, height - 12, width, height], fill=(180, 30, 30))

    # Save baseline ID card at standard scanning JPEG quality (85)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    baseline_bytes = buf.getvalue()

    # If Tampered: Open the already-compressed image, splice an altered DOB text box, and embed editing software signature
    # This precisely recreates the authentic digital forensics pattern of an image altered in Photoshop!
    if tamper_dob:
        tampered_pil = Image.open(io.BytesIO(baseline_bytes)).convert("RGB")
        t_draw = ImageDraw.Draw(tampered_pil)
        # Spliced white box covering original DOB
        t_draw.rectangle([218, 160, 380, 192], fill=(255, 255, 255), outline=(210, 210, 210))
        t_draw.text((220, 165), "DOB: 10/01/2002", fill=(10, 10, 10))
        
        # Add localized pixel perturbation across the patch
        np_arr = np.array(tampered_pil)
        np_arr[160:192, 218:380] = cv2.add(np_arr[160:192, 218:380], np.random.randint(-18, 18, (32, 162, 3), dtype=np.int16).clip(0, 255).astype(np.uint8))
        
        final_img = Image.fromarray(np_arr)
        # Add EXIF software tag for Photoshop
        exif = final_img.getexif()
        exif[0x0131] = "Adobe Photoshop 2024 (Windows)"
        out_buf = io.BytesIO()
        final_img.save(out_buf, format="JPEG", quality=95, exif=exif)
        return out_buf.getvalue()

    # If Blurry: Apply Gaussian blur filter
    if is_blurry:
        b_img = Image.open(io.BytesIO(baseline_bytes))
        b_img = b_img.filter(ImageFilter.GaussianBlur(radius=3.5))
        out_buf = io.BytesIO()
        b_img.save(out_buf, format="JPEG", quality=80)
        return out_buf.getvalue()

    return baseline_bytes


def create_sample_college_id(
    name: str = "AARAV SHARMA",
    college: str = "INDIAN INSTITUTE OF TECHNOLOGY BOMBAY",
    roll_no: str = "21BCE1042",
    dept: str = "Computer Science & Engineering",
    valid_till: str = "2027"
) -> bytes:
    """
    Generates a synthetic Indian University Student Identity Card.
    """
    width, height = 700, 440
    img = Image.new("RGB", (width, height), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)

    # Top College Header Banner
    draw.rectangle([0, 0, width, 75], fill=(26, 54, 93))
    draw.text((70, 18), college, fill=(255, 255, 255))
    draw.text((220, 45), "STUDENT IDENTITY CARD", fill=(203, 213, 225))

    # Portrait photo box
    _draw_synthetic_portrait(draw, (45, 110, 185, 290))

    # Student Details
    draw.text((220, 115), f"Name: {name}", fill=(15, 23, 42))
    draw.text((220, 150), f"Roll No: {roll_no}", fill=(15, 23, 42))
    draw.text((220, 185), f"Department: {dept}", fill=(51, 65, 85))
    draw.text((220, 220), f"Valid Thru: {valid_till}", fill=(51, 65, 85))
    draw.text((220, 255), "DOB: 15/08/2004", fill=(51, 65, 85))

    # Barcode representation
    draw.rectangle([220, 310, 550, 345], fill=(226, 232, 240))
    for x in range(230, 540, 6):
        draw.line([(x, 315), (x, 340)], fill=(0, 0, 0), width=2 if x % 12 == 0 else 1)

    # Footer
    draw.rectangle([0, height - 25, width, height], fill=(30, 41, 59))
    draw.text((250, height - 20), "Cardholder is a verified bona fide student", fill=(148, 163, 184))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def create_sample_selfie(matching: bool = True) -> bytes:
    """
    Generates a live webcam selfie snapshot.
    If matching is False, generates a completely different face to trigger face mismatch!
    """
    width, height = 400, 400
    img = Image.new("RGB", (width, height), color=(235, 240, 245))
    draw = ImageDraw.Draw(img)
    
    # Background room gradient/lines
    draw.rectangle([0, 0, width, height], fill=(230, 235, 242))
    draw.line([(0, 280), (width, 280)], fill=(210, 215, 225), width=2)
    
    # Face
    seed = 42 if matching else 999
    if matching:
        _draw_synthetic_portrait(draw, (90, 60, 310, 350), seed=42)
    else:
        # Very different face (different skin tone, hair, proportions)
        x0, y0, x1, y1 = 110, 70, 290, 330
        w = x1 - x0
        h = y1 - y0
        draw.rectangle([x0, y0, x1, y1], fill=(240, 220, 220), outline=(190, 140, 140), width=2)
        draw.ellipse([x0 + 10, y0 + 10, x1 - 10, y1 - 20], fill=(160, 110, 80)) # Darker skin
        draw.ellipse([x0 + 25, y0 + 50, x0 + 45, y0 + 65], fill=(255, 255, 255))
        draw.ellipse([x1 - 45, y0 + 50, x1 - 25, y0 + 65], fill=(255, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


# --- Pre-generate and Cache Sample Fixtures ---
PRESETS = {
    "valid_student": {
        "title": "Eligible Student (Pass)",
        "description": "21yo IIT Bombay Student with valid Aadhaar + College ID + matching selfie.",
        "applicant_name": "Aarav Sharma",
        "applicant_email": "aarav.sharma@iitb.ac.in",
        "declared_dob": "2004-08-15",
        "declared_college": "IIT Bombay",
        "expected_decision": "APPROVED",
        "id_func": lambda: create_sample_aadhaar(name="AARAV SHARMA", dob="15/08/2004"),
        "selfie_func": lambda: create_sample_selfie(matching=True)
    },
    "underage_applicant": {
        "title": "Underage Candidate (Fail)",
        "description": "15yo applicant (DOB: 2011). Fails minimum age eligibility constraint (18-25).",
        "applicant_name": "Rohan Verma",
        "applicant_email": "rohan.v@schoolmail.com",
        "declared_dob": "2011-04-12",
        "declared_college": "Delhi Public School",
        "expected_decision": "REJECTED",
        "id_func": lambda: create_sample_aadhaar(name="ROHAN VERMA", dob="12/04/2011", aadhaar_11_digits="87654321098"),
        "selfie_func": lambda: create_sample_selfie(matching=True)
    },
    "tampered_dob": {
        "title": "Photoshopped / Tampered DOB (Fraud)",
        "description": "Digitally altered DOB patch. Triggers Error Level Analysis (ELA) tampering alert.",
        "applicant_name": "Vikram Singh",
        "applicant_email": "vikram.s@gmail.com",
        "declared_dob": "2002-01-10",
        "declared_college": "State University",
        "expected_decision": "REJECTED / FLAGGED",
        "id_func": lambda: create_sample_aadhaar(name="VIKRAM SINGH", dob="10/01/2002", tamper_dob=True, aadhaar_11_digits="76543210987"),
        "selfie_func": lambda: create_sample_selfie(matching=True)
    },
    "duplicate_sybil": {
        "title": "Reused ID / Sybil Attack (Fraud)",
        "description": "Candidate attempting to register with an Aadhaar card already used by Aarav Sharma.",
        "applicant_name": "Karan Malhotra",
        "applicant_email": "karan.malhotra99@gmail.com",
        "declared_dob": "2004-08-15",
        "declared_college": "BITS Pilani",
        "expected_decision": "REJECTED (DUPLICATE_ID)",
        "id_func": lambda: create_sample_aadhaar(name="AARAV SHARMA", dob="15/08/2004", aadhaar_11_digits="98432109876"),
        "selfie_func": lambda: create_sample_selfie(matching=True)
    },
    "blurry_photo": {
        "title": "Blurry ID Document (Review Queue)",
        "description": "Camera motion blur. Routed to 1-click organizer manual review rather than hard false rejection.",
        "applicant_name": "Priya Nair",
        "applicant_email": "priya.nair@nitk.edu.in",
        "declared_dob": "2003-11-20",
        "declared_college": "NIT Karnataka",
        "expected_decision": "MANUAL_REVIEW",
        "id_func": lambda: create_sample_aadhaar(name="PRIYA NAIR", dob="20/11/2003", is_blurry=True, aadhaar_11_digits="65432109876"),
        "selfie_func": lambda: create_sample_selfie(matching=True)
    },
    "face_mismatch": {
        "title": "Face Mismatch / Impersonation",
        "description": "Uploaded ID portrait does not match the live webcam selfie of the registrant.",
        "applicant_name": "Aarav Sharma",
        "applicant_email": "aarav.copy@gmail.com",
        "declared_dob": "2004-08-15",
        "declared_college": "IIT Bombay",
        "expected_decision": "MANUAL_REVIEW / FLAGGED",
        "id_func": lambda: create_sample_aadhaar(name="AARAV SHARMA", dob="15/08/2004", aadhaar_11_digits="54321098765"),
        "selfie_func": lambda: create_sample_selfie(matching=False)
    }
}
