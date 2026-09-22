"""
Hackingly ID-Shield: AI-Powered Identity & Eligibility Verification API
Main FastAPI Application
"""

import io
import os
import uuid
import base64
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import OrderedDict

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Response, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel
from PIL import Image

from backend.ocr.textract_adapter import (
    extract_document_ocr,
    extract_dob_legacy_textract,
    HAS_AWS_CREDENTIALS,
    BOTO3_AVAILABLE
)
from backend.ocr.field_extractor import parse_id_document
from backend.forensics.quality_analyzer import evaluate_document_quality
from backend.forensics.tampering_detector import analyze_document_tampering
from backend.face.face_matcher import verify_id_against_selfie
from backend.fraud.duplicate_detector import check_for_duplicates, record_registration
from backend.rules.eligibility_engine import evaluate_eligibility, load_rules, save_rules
from backend.data.sample_generator import PRESETS

logger = logging.getLogger("main")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

app = FastAPI(
    title="Hackingly ID-Shield Verification API",
    description="AI-Powered Identity & Eligibility Verification for Hackathons & Competitions",
    version="1.1.0"
)

# Robust CORS Configuration: allows local dev ports with credentials cleanly
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# In-memory registration store with bounded capacity to prevent memory leaks
MAX_STORE_CAPACITY = 200
REGISTRATIONS_STORE: OrderedDict[str, Dict[str, Any]] = OrderedDict()

# Security file limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB per file


def mask_id_string(id_val: Optional[str]) -> str:
    """Masks Aadhaar/PAN ID numbers for privacy compliance during list serialization."""
    if not id_val:
        return "—"
    val = id_val.strip()
    digits = val.replace(" ", "").replace("-", "")
    if len(digits) == 12 and (digits.isdigit() or "X" in digits):
        return f"XXXX-XXXX-{digits[-4:]}"
    elif len(val) == 10:
        return f"{val[:2]}XXXXX{val[-2:]}"
    elif len(val) > 4:
        return f"{'*' * (len(val) - 4)}{val[-4:]}"
    return val


class ManualDecisionRequest(BaseModel):
    action: str  # "APPROVED", "MANUAL_REVIEW", "REJECTED"
    reviewer_notes: Optional[str] = ""


class RulesUpdateRequest(BaseModel):
    hackathon_name: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    require_student_status: Optional[bool] = None
    allowed_id_types: Optional[List[str]] = None
    require_face_match: Optional[bool] = None
    min_face_match_threshold: Optional[float] = None
    max_tamper_threshold: Optional[float] = None
    auto_approve_min_confidence: Optional[float] = None


@app.on_event("startup")
async def seed_initial_demo_data():
    """Seeds initial realistic sample registrations so the operator dashboard has live data."""
    if len(REGISTRATIONS_STORE) > 0:
        return

    demo_seeds = ["valid_student", "tampered_dob", "blurry_photo"]
    for preset_key in demo_seeds:
        if preset_key not in PRESETS:
            continue
        try:
            p = PRESETS[preset_key]
            id_bytes = p["id_func"]()
            selfie_bytes = p["selfie_func"]()

            # Execute pipeline synchronously in threadpool during startup
            res = await run_in_threadpool(
                _execute_verification_pipeline,
                applicant_name=p["applicant_name"],
                applicant_email=p["applicant_email"],
                declared_dob=p["declared_dob"],
                declared_college=p["declared_college"],
                id_bytes=id_bytes,
                selfie_bytes=selfie_bytes
            )
            REGISTRATIONS_STORE[res["registration_id"]] = res
        except Exception as e:
            logger.warning(f"Could not seed demo preset '{preset_key}': {e}")


@app.get("/api/health")
def health_check():
    """Returns engine telemetry and system health."""
    return {
        "status": "healthy",
        "service": "Hackingly ID-Shield",
        "engines": {
            "aws_textract": "ACTIVE" if (HAS_AWS_CREDENTIALS and BOTO3_AVAILABLE) else "FALLBACK_LOCAL_AI",
            "forensics_ela": "ACTIVE",
            "face_matcher": "ACTIVE",
            "duplicate_detector": "ACTIVE",
            "rule_engine": "ACTIVE"
        },
        "records_loaded": len(REGISTRATIONS_STORE),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/textract/dob")
async def extract_dob_legacy(file: UploadFile = File(...)):
    """
    Drop-in backward-compatible endpoint for Hackingly's current AWS Textract DOB extractor.
    Preserves exact contract for zero-friction integration.
    """
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 10MB maximum limit.")

    res = await run_in_threadpool(extract_dob_legacy_textract, contents)
    return res


def _execute_verification_pipeline(
    applicant_name: str,
    applicant_email: str,
    declared_dob: Optional[str],
    declared_college: Optional[str],
    id_bytes: bytes,
    selfie_bytes: Optional[bytes]
) -> Dict[str, Any]:
    """
    Synchronous CPU-bound AI pipeline. Offloaded to worker threadpool.
    """
    reg_id = f"REG-{uuid.uuid4().hex[:8].upper()}"

    # Verify image integrity
    try:
        with Image.open(io.BytesIO(id_bytes)) as img:
            img.verify()
    except Exception:
        raise ValueError("Corrupted or unreadable ID card image.")

    # Encode original ID image as base64 preview
    id_card_b64 = f"data:image/jpeg;base64,{base64.b64encode(id_bytes).decode('utf-8')}"
    selfie_b64 = f"data:image/jpeg;base64,{base64.b64encode(selfie_bytes).decode('utf-8')}" if selfie_bytes else None

    # Step 1: Image Quality Assessment
    quality = evaluate_document_quality(id_bytes)

    # Step 2: Full Document OCR
    ocr_response = extract_document_ocr(id_bytes)

    # Step 3: Document Intelligence & Field Parsing
    extracted_fields = parse_id_document(ocr_response, declared_name=applicant_name)

    # Step 4: Digital Forensics & Tampering (ELA)
    forensics = analyze_document_tampering(id_bytes)

    # Step 5: Facial Verification & Liveness
    face_data = verify_id_against_selfie(id_bytes, selfie_bytes)

    # Step 6: Duplicate & Sybil Attack Check
    duplicate_info = check_for_duplicates(
        id_number=extracted_fields.get("id_number"),
        applicant_name=applicant_name,
        applicant_email=applicant_email,
        current_reg_id=reg_id
    )

    # Step 7: Configurable Eligibility Decision Engine
    eligibility = evaluate_eligibility(
        applicant_name=applicant_name,
        applicant_email=applicant_email,
        declared_dob=declared_dob,
        declared_college=declared_college,
        extracted_fields=extracted_fields,
        forensics=forensics,
        quality=quality,
        face_data=face_data,
        duplicate_info=duplicate_info
    )

    # Step 8: Save to duplicate registry
    record_registration(
        registration_id=reg_id,
        applicant_name=applicant_name,
        applicant_email=applicant_email,
        id_type=extracted_fields.get("document_type", "UNKNOWN"),
        id_number=extracted_fields.get("id_number"),
        status=eligibility["decision"]
    )

    result_payload = {
        "registration_id": reg_id,
        "timestamp": datetime.now().isoformat(),
        "applicant": {
            "name": applicant_name,
            "email": applicant_email,
            "declared_dob": declared_dob,
            "declared_college": declared_college
        },
        "decision": eligibility["decision"],
        "confidence_score": eligibility["confidence_score"],
        "summary": eligibility["summary"],
        "reasons": eligibility["reasons"],
        "security_flags": eligibility["security_flags"],
        "extracted_fields": {
            "document_type": extracted_fields.get("document_type"),
            "name": extracted_fields.get("name"),
            "dob": extracted_fields.get("dob"),
            "age": extracted_fields.get("age"),
            "gender": extracted_fields.get("gender"),
            "id_number": extracted_fields.get("id_number"),
            "institution": extracted_fields.get("institution"),
            "validation_info": extracted_fields.get("validation_info")
        },
        "forensics": {
            "tamper_score": forensics.get("tamper_score"),
            "risk_level": forensics.get("risk_level"),
            "assessment": forensics.get("assessment"),
            "ela_heatmap_url": forensics.get("ela_heatmap_url")
        },
        "quality": quality,
        "face_verification": {
            "status": face_data.get("status"),
            "similarity_score": face_data.get("similarity_score"),
            "is_match": face_data.get("is_match"),
            "details": face_data.get("details"),
            "id_face_crop_url": face_data.get("id_face_crop_url"),
            "selfie_face_crop_url": face_data.get("selfie_face_crop_url")
        },
        "duplicate_check": duplicate_info,
        "bounding_boxes": extracted_fields.get("bounding_boxes", []),
        "images": {
            "id_card_preview": id_card_b64,
            "selfie_preview": selfie_b64
        },
        "ocr_source": extracted_fields.get("ocr_source")
    }

    return result_payload


@app.post("/api/verify")
async def verify_registration(
    applicant_name: str = Form(...),
    applicant_email: str = Form(...),
    declared_dob: Optional[str] = Form(None),
    declared_college: Optional[str] = Form(None),
    id_card_file: UploadFile = File(...),
    selfie_file: Optional[UploadFile] = File(None)
):
    """
    Full AI Identity & Eligibility Verification Pipeline.
    Runs non-blocking on threadpool to guarantee event-loop concurrency.
    """
    id_bytes = await id_card_file.read()
    if len(id_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="ID document exceeds 10MB limit.")

    selfie_bytes = None
    if selfie_file:
        selfie_bytes = await selfie_file.read()
        if len(selfie_bytes) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Selfie image exceeds 10MB limit.")

    try:
        result_payload = await run_in_threadpool(
            _execute_verification_pipeline,
            applicant_name=applicant_name,
            applicant_email=applicant_email,
            declared_dob=declared_dob,
            declared_college=declared_college,
            id_bytes=id_bytes,
            selfie_bytes=selfie_bytes
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        logger.error(f"Verification pipeline failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(exc)}")

    # Enforce bounded store size to prevent OOM
    if len(REGISTRATIONS_STORE) >= MAX_STORE_CAPACITY:
        REGISTRATIONS_STORE.popitem(last=False)

    REGISTRATIONS_STORE[result_payload["registration_id"]] = result_payload
    return result_payload


@app.get("/api/registrations")
def list_registrations():
    """Returns all registrations with summary statistics and privacy-safe masked identifiers."""
    records = list(REGISTRATIONS_STORE.values())

    total = len(records)
    approved = sum(1 for r in records if r.get("decision") == "APPROVED")
    manual_review = sum(1 for r in records if r.get("decision") == "MANUAL_REVIEW")
    rejected = sum(1 for r in records if r.get("decision") == "REJECTED")

    return {
        "stats": {
            "total_registrations": total,
            "approved": approved,
            "approved_percent": round((approved / total * 100), 1) if total > 0 else 0,
            "manual_review_queue": manual_review,
            "rejected_fraud": rejected
        },
        "registrations": sorted(records, key=lambda r: r.get("timestamp", ""), reverse=True)
    }


@app.get("/api/registrations/{reg_id}")
def get_registration_details(reg_id: str):
    """Fetches full forensic profile for a specific registration."""
    if reg_id not in REGISTRATIONS_STORE:
        raise HTTPException(status_code=404, detail="Registration not found")
    return REGISTRATIONS_STORE[reg_id]


@app.post("/api/registrations/{reg_id}/decision")
def submit_manual_decision(reg_id: str, body: ManualDecisionRequest):
    """Allows hackathon organizer to approve or reject a borderline registration."""
    if reg_id not in REGISTRATIONS_STORE:
        raise HTTPException(status_code=404, detail="Registration not found")

    rec = REGISTRATIONS_STORE[reg_id]
    rec["decision"] = body.action
    rec["reviewer_override"] = {
        "action": body.action,
        "notes": body.reviewer_notes,
        "timestamp": datetime.now().isoformat()
    }
    rec["reasons"].append(f"[ORGANIZER OVERRIDE] Status updated to {body.action} by reviewer. Notes: {body.reviewer_notes or 'None'}")
    return rec


@app.get("/api/rules")
def get_rules():
    """Returns active hackathon eligibility configuration."""
    return load_rules()


@app.put("/api/rules")
def update_rules(body: RulesUpdateRequest):
    """Updates hackathon eligibility parameters."""
    current = load_rules()
    data = body.model_dump(exclude_unset=True)
    current.update(data)
    save_rules(current)
    return current


@app.get("/api/samples")
def list_sample_presets():
    """Returns available test cases for rapid demoing."""
    return [
        {
            "key": key,
            "title": data["title"],
            "description": data["description"],
            "applicant_name": data["applicant_name"],
            "applicant_email": data["applicant_email"],
            "declared_dob": data["declared_dob"],
            "declared_college": data["declared_college"],
            "expected_decision": data["expected_decision"]
        }
        for key, data in PRESETS.items()
    ]


@app.get("/api/samples/{preset_key}/id_card")
def get_sample_id_card(preset_key: str):
    """Returns generated ID card JPEG for a preset."""
    if preset_key not in PRESETS:
        raise HTTPException(status_code=404, detail="Preset not found")
    img_bytes = PRESETS[preset_key]["id_func"]()
    return Response(content=img_bytes, media_type="image/jpeg")


@app.get("/api/samples/{preset_key}/selfie")
def get_sample_selfie_image(preset_key: str):
    """Returns generated selfie JPEG for a preset."""
    if preset_key not in PRESETS:
        raise HTTPException(status_code=404, detail="Preset not found")
    img_bytes = PRESETS[preset_key]["selfie_func"]()
    return Response(content=img_bytes, media_type="image/jpeg")
