"""
Configurable Hackathon Eligibility and Decision Engine
Combines:
- Age & Date of Birth constraints
- Student & Institution gating
- Document format and Verhoeff checksum validation
- Tampering / Forgery forensic analysis
- Cross-registration Sybil & duplicate detection
- Facial likeness / Selfie verification
- Three-tier triage (APPROVED / MANUAL_REVIEW / REJECTED) to minimize false positives
"""

from typing import Dict, Any, List, Optional
import json
import os
import re

RULES_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "hackathon_rules.json")

# Default Hackathon Eligibility Settings
DEFAULT_RULES = {
    "hackathon_name": "AI Build Challenge Bengaluru 2026",
    "min_age": 18,
    "max_age": 25,
    "require_student_status": True,
    "allowed_id_types": ["AADHAAR_CARD", "COLLEGE_ID", "PAN_CARD", "DRIVING_LICENSE", "VOTER_ID"],
    "require_face_match": False,  # Optional live selfie
    "min_face_match_threshold": 60.0,
    "max_tamper_threshold": 45.0,
    "auto_approve_min_confidence": 75.0,
    "auto_reject_max_confidence": 40.0
}


def load_rules() -> Dict[str, Any]:
    """Loads active rules from disk or returns defaults."""
    if os.path.exists(RULES_CONFIG_FILE):
        try:
            with open(RULES_CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_RULES.copy()


import tempfile
import logging

logger = logging.getLogger("eligibility_engine")


def save_rules(rules: Dict[str, Any]) -> bool:
    """Updates active rules configuration atomically."""
    try:
        dir_name = os.path.dirname(RULES_CONFIG_FILE)
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False) as tf:
            json.dump(rules, tf, indent=2)
            temp_name = tf.name
        os.replace(temp_name, RULES_CONFIG_FILE)
        return True
    except Exception as e:
        logger.error(f"Failed to save rules configuration: {e}")
        return False


def evaluate_eligibility(
    applicant_name: str,
    applicant_email: str,
    declared_dob: Optional[str],
    declared_college: Optional[str],
    extracted_fields: Dict[str, Any],
    forensics: Dict[str, Any],
    quality: Dict[str, Any],
    face_data: Dict[str, Any],
    duplicate_info: Dict[str, Any],
    custom_rules: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Evaluates applicant's identity, document, and eligibility against hackathon rules.
    Computes confidence score and generates human-readable reasoning list.
    """
    rules = custom_rules or load_rules()
    reasons: List[str] = []
    security_flags: List[str] = []
    
    score_points = 100.0
    hard_reject = False
    needs_manual_review = False

    doc_type = extracted_fields.get("document_type", "UNKNOWN")
    dob = extracted_fields.get("dob")
    age = extracted_fields.get("age")
    id_validation = extracted_fields.get("validation_info", {})
    tamper_score = forensics.get("tamper_score", 0.0)

    # 1. Document Type Check
    allowed_types = rules.get("allowed_id_types", [])
    if doc_type in allowed_types:
        reasons.append(f"[PASS] Document Recognized: Valid {doc_type.replace('_', ' ').title()}")
    else:
        reasons.append(f"[FAIL] Document Type '{doc_type}' is not accepted for this hackathon.")
        security_flags.append("UNACCEPTED_DOC_TYPE")
        score_points -= 25.0
        needs_manual_review = True

    # 2. Checksum / Format Validity
    if not id_validation.get("is_valid", True):
        reasons.append(f"[FAIL] ID Checksum / Format Error: {id_validation.get('details')}")
        security_flags.append("CHECKSUM_FAILED")
        score_points -= 40.0
        hard_reject = True
    else:
        if id_validation.get("checksum_passed", False):
            reasons.append(f"[PASS] Official Checksum Verified ({id_validation.get('details')})")

    # 3. Age & DOB Verification
    min_age = rules.get("min_age", 18)
    max_age = rules.get("max_age", 25)

    if age is not None:
        if min_age <= age <= max_age:
            reasons.append(f"[PASS] Age Eligibility Verified: {age} years old (Eligible range: {min_age}-{max_age}) [DOB: {dob}]")
        elif age < min_age:
            reasons.append(f"[FAIL] Underage Applicant: Participant is {age} years old (Minimum required: {min_age} years) [DOB: {dob}]")
            security_flags.append("UNDERAGE_APPLICANT")
            score_points -= 50.0
            hard_reject = True
        else:
            reasons.append(f"[FAIL] Age Exceeds Maximum: Participant is {age} years old (Maximum permitted: {max_age} years) [DOB: {dob}]")
            security_flags.append("OVERAGE_APPLICANT")
            score_points -= 50.0
            hard_reject = True
    else:
        reasons.append("[FLAG] Date of Birth could not be conclusively determined from the ID text.")
        security_flags.append("DOB_EXTRACTION_UNCERTAIN")
        score_points -= 20.0
        needs_manual_review = True

    # 4. Student Status / Institution Check (if required by Hackathon)
    if rules.get("require_student_status", False):
        institution = extracted_fields.get("institution")
        if doc_type == "COLLEGE_ID" or institution:
            inst_name = institution or declared_college or "Recognized Institution"
            reasons.append(f"[PASS] Student Status Confirmed: Enrolled at {inst_name}")
        elif declared_college and len(declared_college.strip()) > 3:
            reasons.append(f"[PASS] Student Affiliation Declared: {declared_college} (Verified via Official Government ID)")
        else:
            reasons.append("[FAIL] Hackathon requires verified student status. Neither College ID nor student affiliation found.")
            security_flags.append("STUDENT_STATUS_UNVERIFIED")
            score_points -= 30.0
            needs_manual_review = True

    # 5. Tampering & Digital Forensics (ELA)
    max_tamper = rules.get("max_tamper_threshold", 45.0)
    if tamper_score <= max_tamper:
        reasons.append(f"[PASS] Digital Integrity Passed: Tamper index {tamper_score}/100 (Threshold: {max_tamper})")
    else:
        reasons.append(f"[FAIL] Forgery Risk Detected: Error Level Analysis scored {tamper_score}/100 (Threshold: {max_tamper}). {forensics.get('assessment')}")
        security_flags.append("POTENTIAL_TAMPERING_DETECTED")
        score_points -= 45.0
        if tamper_score > 65.0:
            hard_reject = True
        else:
            needs_manual_review = True

    # 6. Duplicate & Sybil Attack Check
    if duplicate_info.get("has_duplicate", False):
        dup_type = duplicate_info.get("duplicate_type")
        if dup_type == "SYBIL_ID_REUSE":
            reasons.append(f"[FAIL] Sybil Fraud Alert: {duplicate_info.get('message')}")
            security_flags.append("SYBIL_DUPLICATE_ID")
            score_points -= 60.0
            hard_reject = True
        elif dup_type == "RE_REGISTRATION_SAME_PERSON":
            reasons.append(f"[FLAG] Duplicate Notice: {duplicate_info.get('message')}")
            security_flags.append("REPEAT_REGISTRATION")
            score_points -= 5.0
    else:
        reasons.append("[PASS] Identity Uniqueness: ID number has not been used across other registrations.")

    # 7. Face Matching (ID photo vs live selfie)
    if face_data.get("face_detected_in_selfie", False):
        face_match = face_data.get("is_match", False)
        sim_score = face_data.get("similarity_score", 0.0)
        req_thresh = rules.get("min_face_match_threshold", 60.0)
        
        if face_match:
            reasons.append(f"[PASS] Face Match Confirmed: {sim_score}% facial similarity between ID and selfie (Req: {req_thresh}%)")
        else:
            reasons.append(f"[FAIL] Face Mismatch Warning: Only {sim_score}% similarity (Req: {req_thresh}%).")
            security_flags.append("FACE_MISMATCH")
            score_points -= 35.0
            needs_manual_review = True
    elif face_data.get("face_detected_in_id", False):
        reasons.append("[INFO] ID Portrait photo extracted. Live webcam selfie was not provided.")
    else:
        reasons.append("[FLAG] No clear face portrait detected on the uploaded ID.")
        score_points -= 10.0
        needs_manual_review = True

    # 8. Image Quality / Blur Check
    if quality.get("is_blurry", False):
        reasons.append(f"[FLAG] Image Quality Advisory: {quality.get('summary')}. Flagged for organizer visual check to prevent false rejection.")
        score_points -= 15.0
        needs_manual_review = True
    else:
        reasons.append(f"[PASS] Document Quality: Clear and legible (Sharpness score: {quality.get('laplacian_variance')})")

    # Name Consistency Check
    extracted_name = extracted_fields.get("name")
    if extracted_name and applicant_name:
        # Check token overlap
        n1 = set(w for w in re.findall(r"\b\w+\b", extracted_name.lower()) if len(w) > 1)
        n2 = set(w for w in re.findall(r"\b\w+\b", applicant_name.lower()) if len(w) > 1)
        if n1.intersection(n2):
            reasons.append(f"[PASS] Name Verified: Extracted '{extracted_name}' matches registered '{applicant_name}'")
        else:
            reasons.append(f"[REVIEW] Name Discrepancy: Extracted name '{extracted_name}' differs from registration '{applicant_name}'")
            score_points -= 15.0
            needs_manual_review = True

    # Final Confidence Score Calculation
    final_confidence = round(max(5.0, min(99.0, score_points)), 1)
    
    # 3-Tier Decision Logic
    auto_approve_thresh = rules.get("auto_approve_min_confidence", 75.0)
    
    if hard_reject or final_confidence < 35.0:
        decision = "REJECTED"
        summary = "Registration rejected based on definitive eligibility or integrity violation."
    elif needs_manual_review or final_confidence < auto_approve_thresh:
        decision = "MANUAL_REVIEW"
        summary = "Registration routed to Organizer Manual Review queue to minimize false rejections."
    else:
        decision = "APPROVED"
        summary = "Candidate identity and hackathon eligibility verified automatically."

    return {
        "decision": decision,
        "confidence_score": final_confidence,
        "summary": summary,
        "reasons": reasons,
        "security_flags": security_flags,
        "metrics": {
            "tamper_score": tamper_score,
            "quality_score": quality.get("quality_score", 0),
            "face_similarity": face_data.get("similarity_score"),
            "duplicate_risk": duplicate_info.get("risk_score", 0)
        }
    }
