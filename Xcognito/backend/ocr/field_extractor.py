"""
Field Extractor for Indian Identity Documents
Extracts and normalizes:
- Document Type (Aadhaar, College ID, PAN, Driving License, Voter ID)
- Name, Date of Birth (DOB), Computed Age, Gender
- ID Number (with format/Verhoeff validation)
- Educational Institution / College Name
- Bounding boxes for visual inspection in the organizer UI
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.ocr.checksums import validate_aadhaar, validate_pan, validate_college_id

CURRENT_YEAR = 2026

# Known Institution keywords for Indian colleges & universities
COLLEGE_KEYWORDS = [
    "INSTITUTE OF TECHNOLOGY", "UNIVERSITY", "COLLEGE", "CAMPUS",
    "IIT", "NIT", "BITS", "IIIT", "POLYTECHNIC", "ACADEMY", "VIDYAPEETH",
    "ENGINEERING", "TECHNOLOGICAL", "B.TECH", "M.TECH", "B.E.", "STUDENT ID",
    "DEPARTMENT OF", "MASTERS' UNION", "DELHI TECHNOLOGICAL"
]


def detect_document_type(text_lines: List[str]) -> str:
    """
    Classifies document type based on key phrases and regex patterns.
    """
    full_text = " ".join(text_lines).upper()

    if any(k in full_text for k in ["AADHAAR", "UIDAI", "MERA AADHAAR", "GOVERNMENT OF INDIA", "UNIQUE IDENTIFICATION AUTHORITY"]):
        return "AADHAAR_CARD"

    if any(k in full_text for k in ["INCOME TAX DEPARTMENT", "PERMANENT ACCOUNT NUMBER", "FATHER'S NAME"]) and re.search(r"[A-Z]{5}[0-9]{4}[A-Z]", full_text):
        return "PAN_CARD"

    if any(k in full_text for k in COLLEGE_KEYWORDS) or any(k in full_text for k in ["STUDENT ID", "ROLL NO", "ENROLLMENT NO", "SEMESTER", "STUDENT CARD"]):
        return "COLLEGE_ID"

    if any(k in full_text for k in ["ELECTION COMMISSION", "ELECTOR PHOTO IDENTITY", "EPIC"]):
        return "VOTER_ID"

    if any(k in full_text for k in ["DRIVING LICENCE", "DRIVING LICENSE", "UNION OF INDIA DRIVING", "MOTOR VEHICLES"]):
        return "DRIVING_LICENSE"

    # Fallback to pattern matching
    if re.search(r"\b\d{4}\s\d{4}\s\d{4}\b", full_text) or re.search(r"[xX]{4}\s?[xX]{4}\s?\d{4}", full_text):
        return "AADHAAR_CARD"
    if re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", full_text):
        return "PAN_CARD"

    return "OTHER_GOVT_ID"


def extract_dob_and_age(text_lines: List[str]) -> Dict[str, Any]:
    """
    Finds DOB patterns (DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, YYYY) and calculates age.
    """
    dob_regex = r"(?:DOB|D\.O\.B|Date of Birth|Birth Date|Year of Birth|जन्म तारीख|जन्म वर्ष)[:\s]*([0-9]{1,4}[/\-\.][0-9]{1,2}[/\-\.][0-9]{1,4}|[0-9]{4})"
    standalone_date_regex = r"\b([0-3]?[0-9][/\-\.][0-1]?[0-9][/\-\.](?:19|20)[0-9]{2})\b"
    iso_date_regex = r"\b((?:19|20)[0-9]{2}[/\-\.][0-1]?[0-9][/\-\.][0-3]?[0-9])\b"
    year_only_regex = r"(?:Year of Birth|YOB)[:\s]*((?:19|20)[0-9]{2})\b"

    extracted_dob = None
    extracted_age = None
    matched_line = None

    for line in text_lines:
        # First priority: labelled DOB
        m = re.search(dob_regex, line, re.IGNORECASE)
        if m:
            extracted_dob = m.group(1).replace("-", "/").replace(".", "/")
            matched_line = line
            break
        # Second priority: explicit year of birth
        m_yob = re.search(year_only_regex, line, re.IGNORECASE)
        if m_yob:
            extracted_dob = m_yob.group(1)
            matched_line = line
            break

    # If not found, look for standard standalone date patterns
    if not extracted_dob:
        for line in text_lines:
            m_date = re.search(standalone_date_regex, line)
            if m_date:
                extracted_dob = m_date.group(1).replace("-", "/").replace(".", "/")
                matched_line = line
                break
            m_iso = re.search(iso_date_regex, line)
            if m_iso:
                extracted_dob = m_iso.group(1).replace("-", "/").replace(".", "/")
                matched_line = line
                break

    if extracted_dob:
        try:
            if len(extracted_dob) == 4 and extracted_dob.isdigit():
                year = int(extracted_dob)
            else:
                parts = extracted_dob.split("/")
                if len(parts) >= 3:
                    if len(parts[0]) == 4 and parts[0].isdigit():
                        year = int(parts[0])
                    elif len(parts[2]) == 4 and parts[2].isdigit():
                        year = int(parts[2])
                    else:
                        year = int(parts[-1])
                else:
                    year = int(parts[-1])
            if 1900 <= year <= CURRENT_YEAR:
                extracted_age = CURRENT_YEAR - year
        except Exception:
            pass

    return {
        "dob": extracted_dob,
        "age": extracted_age,
        "evidence_line": matched_line
    }


def extract_gender(text_lines: List[str]) -> Optional[str]:
    """
    Detects Gender field from text lines.
    """
    for line in text_lines:
        u = line.upper()
        if re.search(r"\b(FEMALE|WOMAN)\b", u) or (re.search(r"\bF\b", u) and ("GENDER" in u or "SEX" in u)):
            return "FEMALE"
        if re.search(r"\b(MALE|MAN)\b", u) or (re.search(r"\bM\b", u) and ("GENDER" in u or "SEX" in u)):
            return "MALE"
        if "TRANSGENDER" in u:
            return "TRANSGENDER"
    return None


def extract_aadhaar_number(text_lines: List[str]) -> Optional[str]:
    """
    Extracts 12-digit or masked Aadhaar format.
    Handles variable spacing, hyphens, and multi-line OCR artifacts.
    """
    full_text = "\n".join(text_lines)
    
    # 1. Masked format: XXXX XXXX 1234 or **** **** 1234 or XXXXXXXX1234
    m_mask = re.search(r"\b([xX\*]{4}[\s\-]*[xX\*]{4}[\s\-]*\d{4})\b", full_text)
    if m_mask:
        raw_mask = re.sub(r"[\s\-]", "", m_mask.group(1))
        return f"XXXX XXXX {raw_mask[-4:]}"

    # 2. Standard 4-4-4 formatted: 1234 5678 9012 or 1234-5678-9012
    m1 = re.search(r"\b(\d{4})[\s\-]+(\d{4})[\s\-]+(\d{4})\b", full_text)
    if m1:
        return f"{m1.group(1)} {m1.group(2)} {m1.group(3)}"
    
    # 3. 4-8 or 8-4 formats (common in EasyOCR when space inside a group is missed)
    m2 = re.search(r"\b(\d{4})[\s\-]+(\d{8})\b", full_text)
    if m2:
        return f"{m2.group(1)} {m2.group(2)[:4]} {m2.group(2)[4:]}"
    m3 = re.search(r"\b(\d{8})[\s\-]+(\d{4})\b", full_text)
    if m3:
        return f"{m3.group(1)[:4]} {m3.group(1)[4:]} {m3.group(2)}"

    # 4. Check individual lines for any sequence of 12 digits
    for line in text_lines:
        digits_only = re.sub(r"\D", "", line)
        if len(digits_only) == 12:
            if digits_only[0] not in ('0', '1'):
                return f"{digits_only[:4]} {digits_only[4:8]} {digits_only[8:]}"

    # 5. Contiguous 12 digits anywhere in text
    m4 = re.search(r"\b(\d{12})\b", full_text)
    if m4:
        digits = m4.group(1)
        return f"{digits[:4]} {digits[4:8]} {digits[8:]}"

    return None


def extract_pan_number(text_lines: List[str]) -> Optional[str]:
    """
    Extracts Indian PAN 10-char alphanumeric string.
    """
    full_text = "\n".join(text_lines).upper()
    match = re.search(r"\b([A-Z]{5}[0-9]{4}[A-Z])\b", full_text)
    if match:
        return match.group(1)
    return None


def extract_institution(text_lines: List[str]) -> Optional[str]:
    """
    Identifies educational institution / college name from document.
    """
    for line in text_lines:
        u = line.upper()
        if any(k in u for k in COLLEGE_KEYWORDS):
            # Clean up line
            cleaned = re.sub(r"(STUDENT IDENTITY CARD|STUDENT ID|IDENTITY CARD|COLLEGE ID)", "", line, flags=re.IGNORECASE).strip()
            if len(cleaned) > 4:
                return cleaned
    return None


def extract_student_roll(text_lines: List[str]) -> Optional[str]:
    """
    Extracts Roll Number, Enrollment ID, or Student Registration ID.
    """
    patterns = [
        r"(?:ROLL NO|ROLL NUMBER|ENROLLMENT NO|ID NO|REG NO|STUDENT NO)[:\s]*([A-Z0-9\-\/]+)",
        r"\b([0-9]{2}[A-Z]{2,4}[0-9]{3,5})\b", # e.g. 21BCS045
        r"\b([A-Z]{2,4}/[0-9]{4}/[0-9]{2,4})\b"
    ]
    for line in text_lines:
        for p in patterns:
            m = re.search(p, line, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                if len(val) >= 4 and not val.lower().startswith("dob"):
                    return val
    return None


def extract_name(text_lines: List[str], doc_type: str, declared_name: Optional[str] = None) -> Optional[str]:
    """
    Heuristic name extraction based on Indian ID layouts.
    Strips label prefixes (e.g. 'Name:', 'Student Name:') and matches against declared name.
    """
    ignore_phrases = [
        "GOVERNMENT OF INDIA", "BHARAT SARKAR", "UNIQUE IDENTIFICATION",
        "INCOME TAX DEPARTMENT", "GOVT OF INDIA", "PERMANENT ACCOUNT NUMBER",
        "ELECTION COMMISSION", "STUDENT IDENTITY CARD", "IDENTITY CARD",
        "ENROLLMENT", "SIGNATURE", "AUTHORITY OF INDIA", "MERA AADHAAR",
        "HELP@UIDAI.GOV.IN", "WWW.UIDAI.GOV.IN", "FATHER'S NAME", "DATE OF BIRTH",
        "MERI PEHCHAN", "MALE", "FEMALE", "TRANSGENDER", "ADDRESS", "ROLL NO",
        "DEPARTMENT", "VALID THRU", "CARDHOLDER", "PRINCIPAL", "DIRECTOR"
    ]

    candidates = []
    for line in text_lines:
        raw_line = line.strip()
        if len(raw_line) < 3 or len(raw_line) > 50:
            continue
        
        # Strip common field label prefixes
        clean = re.sub(r"^(?:Candidate|Student|Card\s*Holder|Account\s*Holder|Full)?\s*Name\s*[:\-\.]\s*", "", raw_line, flags=re.IGNORECASE).strip()
        clean = re.sub(r"^नाम\s*[:\-\.]\s*", "", clean).strip()
        clean = clean.strip(": -.,'\"")
        
        u = clean.upper()
        if len(clean) < 3 or len(clean) > 45:
            continue
        if any(ig in u for ig in ignore_phrases):
            continue
        if re.search(r"\d", clean):  # names do not contain digits
            continue
        if re.search(r"\b(DOB|MALE|FEMALE|GENDER|FATHER|YEAR|ADDRESS|ROLL|DEPT)\b", u):
            continue
        
        # Names are mostly alphabetic
        alpha_count = sum(1 for c in clean if c.isalpha() or c.isspace())
        if alpha_count / len(clean) > 0.85:
            candidates.append(clean)

    # If declared name exists, prioritize candidate with highest token overlap
    if declared_name and candidates:
        dec_tokens = set(re.findall(r"\b\w+\b", declared_name.lower()))
        best_cand = None
        best_score = 0
        for cand in candidates:
            cand_tokens = set(re.findall(r"\b\w+\b", cand.lower()))
            intersection = dec_tokens.intersection(cand_tokens)
            if len(intersection) > best_score:
                best_score = len(intersection)
                best_cand = cand
        if best_score > 0 and best_cand:
            return best_cand

    # Default to first plausible candidate
    return candidates[0] if candidates else None


def parse_id_document(ocr_response: Optional[Dict[str, Any]], declared_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Master parsing orchestrator for an extracted OCR document.
    """
    if not ocr_response or not isinstance(ocr_response, dict):
        ocr_response = {"Blocks": []}
    blocks = ocr_response.get("Blocks", [])
    text_lines = []
    bounding_boxes = []

    for block in blocks:
        if block.get("BlockType") == "LINE":
            text = block.get("Text", "").strip()
            if text:
                text_lines.append(text)
                bbox = block.get("Geometry", {}).get("BoundingBox", {})
                bounding_boxes.append({
                    "text": text,
                    "box": bbox,
                    "confidence": block.get("Confidence", 90.0)
                })

    doc_type = detect_document_type(text_lines)
    dob_data = extract_dob_and_age(text_lines)
    gender = extract_gender(text_lines)
    extracted_name = extract_name(text_lines, doc_type, declared_name)
    
    # ID Number extraction & validation
    id_number = None
    validation_info = {"is_valid": True, "details": "Not validated"}

    if doc_type == "AADHAAR_CARD":
        id_number = extract_aadhaar_number(text_lines)
        if id_number:
            validation_info = validate_aadhaar(id_number)
    elif doc_type == "PAN_CARD":
        id_number = extract_pan_number(text_lines)
        if id_number:
            validation_info = validate_pan(id_number)
    elif doc_type == "COLLEGE_ID":
        id_number = extract_student_roll(text_lines)
        if id_number:
            validation_info = validate_college_id(id_number)
    else:
        # Fallback search for any ID number pattern
        id_number = extract_aadhaar_number(text_lines) or extract_pan_number(text_lines) or extract_student_roll(text_lines)

    institution = extract_institution(text_lines) if doc_type == "COLLEGE_ID" else None

    return {
        "document_type": doc_type,
        "name": extracted_name,
        "dob": dob_data.get("dob"),
        "age": dob_data.get("age"),
        "gender": gender,
        "id_number": id_number,
        "institution": institution,
        "validation_info": validation_info,
        "raw_lines": text_lines,
        "bounding_boxes": bounding_boxes,
        "ocr_source": ocr_response.get("Source", "Standard OCR")
    }
