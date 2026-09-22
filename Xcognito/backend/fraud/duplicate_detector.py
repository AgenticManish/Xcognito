"""
Cross-Registration Duplicate and Fraud Detection Engine
Detects:
- Same ID document / ID number reused across different registrations (Sybil attacks)
- Same ID used under different names (identity theft / impersonation)
- Multi-accounting across teams or hackathons
"""

import hashlib
import sqlite3
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

import logging
logger = logging.getLogger("duplicate_detector")

DB_FILE = os.path.join(os.path.dirname(__file__), "registrations.db")


def get_db_connection() -> sqlite3.Connection:
    """Returns a SQLite connection configured for concurrent access with WAL mode."""
    conn = sqlite3.connect(DB_FILE, timeout=15.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def _init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registration_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registration_id TEXT UNIQUE,
            applicant_name TEXT,
            applicant_email TEXT,
            id_type TEXT,
            id_number_norm TEXT,
            id_number_hash TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_id_norm ON registration_registry(id_number_norm)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_email ON registration_registry(applicant_email)")
    conn.commit()
    conn.close()

# Initialize database schema
_init_db()


def _normalize_id(id_number: Optional[str]) -> str:
    """Normalizes ID strings for collision matching (removes spaces, hyphens, uppercase)."""
    if not id_number:
        return ""
    return re.sub(r"[\s\-_]", "", id_number).upper()


def _hash_id(id_number_norm: str) -> str:
    """SHA-256 hash of normalized ID for privacy-safe storage and matching."""
    return hashlib.sha256(id_number_norm.encode("utf-8")).hexdigest()


def check_for_duplicates(
    id_number: Optional[str],
    applicant_name: str,
    applicant_email: str,
    current_reg_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Checks if this ID number or applicant identity has already been registered in the system.
    Detects Sybil attacks (same ID used by different people).
    """
    if not id_number:
        return {
            "has_duplicate": False,
            "duplicate_type": "NONE",
            "risk_score": 0,
            "message": "No ID number extracted for collision check."
        }

    norm_id = _normalize_id(id_number)
    # If masked ID or too short, skip strict duplication check
    if len(norm_id) < 5 or norm_id.startswith("XXXX"):
        return {
            "has_duplicate": False,
            "duplicate_type": "MASKED_SKIPPED",
            "risk_score": 0,
            "message": "Masked ID - duplicate cross-check skipped to protect privacy."
        }

    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT registration_id, applicant_name, applicant_email, status, created_at
        FROM registration_registry
        WHERE id_number_norm = ?
    """
    params = [norm_id]
    if current_reg_id:
        query += " AND registration_id != ?"
        params.append(current_reg_id)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {
            "has_duplicate": False,
            "duplicate_type": "NONE",
            "risk_score": 0,
            "message": "ID number is unique. No prior submissions detected across Hackingly platform."
        }

    # Analyze collisions
    duplicate_records = []
    sybil_detected = False

    clean_current_name = applicant_name.strip().lower()

    for r in rows:
        reg_id, existing_name, existing_email, status, created_at = r
        clean_existing_name = existing_name.strip().lower()
        
        # Check name token overlap
        tokens_curr = set(clean_current_name.split())
        tokens_exist = set(clean_existing_name.split())
        is_same_person = len(tokens_curr.intersection(tokens_exist)) > 0 or clean_current_name == clean_existing_name

        if not is_same_person:
            sybil_detected = True

        duplicate_records.append({
            "registration_id": reg_id,
            "prior_name": existing_name,
            "prior_email": existing_email,
            "status": status,
            "date": created_at,
            "same_person": is_same_person
        })

    if sybil_detected:
        first_conflict = [d for d in duplicate_records if not d["same_person"]][0]
        return {
            "has_duplicate": True,
            "duplicate_type": "SYBIL_ID_REUSE",
            "risk_score": 95,
            "prior_name": first_conflict["prior_name"],
            "prior_registration_id": first_conflict["registration_id"],
            "message": f"CRITICAL FRAUD ALERT: This ID was previously submitted under another identity ({first_conflict['prior_name']}) on {first_conflict['date']}!",
            "duplicate_records": duplicate_records
        }
    else:
        return {
            "has_duplicate": True,
            "duplicate_type": "RE_REGISTRATION_SAME_PERSON",
            "risk_score": 25,
            "prior_name": duplicate_records[0]["prior_name"],
            "prior_registration_id": duplicate_records[0]["registration_id"],
            "message": f"Repeat registration detected: This participant ({duplicate_records[0]['prior_name']}) previously submitted this ID on {duplicate_records[0]['date']}.",
            "duplicate_records": duplicate_records
        }


def record_registration(
    registration_id: str,
    applicant_name: str,
    applicant_email: str,
    id_type: str,
    id_number: Optional[str],
    status: str
) -> bool:
    """Stores a registration in the fraud registry database."""
    if not id_number:
        return False

    norm_id = _normalize_id(id_number)
    id_hash = _hash_id(norm_id)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO registration_registry 
            (registration_id, applicant_name, applicant_email, id_type, id_number_norm, id_number_hash, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (registration_id, applicant_name, applicant_email, id_type, norm_id, id_hash, status))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error saving to registry: {e}")
        return False
    finally:
        conn.close()
