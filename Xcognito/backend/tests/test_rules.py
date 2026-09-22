import unittest
from backend.rules.eligibility_engine import evaluate_eligibility, DEFAULT_RULES

class TestEligibilityEngine(unittest.TestCase):
    def setUp(self):
        self.rules = DEFAULT_RULES.copy()

    def test_eligible_student_approved(self):
        res = evaluate_eligibility(
            applicant_name="Aarav Sharma",
            applicant_email="aarav@iitb.ac.in",
            declared_dob="2004-08-15",
            declared_college="IIT Bombay",
            extracted_fields={
                "document_type": "AADHAAR_CARD",
                "name": "AARAV SHARMA",
                "dob": "15/08/2004",
                "age": 22,
                "institution": "IIT Bombay",
                "validation_info": {"is_valid": True, "checksum_passed": True, "details": "Valid"}
            },
            forensics={"tamper_score": 14.5, "is_flagged": False, "assessment": "Authentic"},
            quality={"quality_score": 90.0, "is_blurry": False, "laplacian_variance": 180.0},
            face_data={"is_match": True, "face_detected_in_selfie": True, "similarity_score": 92.0},
            duplicate_info={"has_duplicate": False, "risk_score": 0},
            custom_rules=self.rules
        )
        self.assertEqual(res["decision"], "APPROVED")
        self.assertGreaterEqual(res["confidence_score"], 85.0)

    def test_underage_applicant_rejected(self):
        res = evaluate_eligibility(
            applicant_name="Rohan Verma",
            applicant_email="rohan@school.com",
            declared_dob="2011-04-12",
            declared_college="School",
            extracted_fields={
                "document_type": "AADHAAR_CARD",
                "name": "ROHAN VERMA",
                "dob": "12/04/2011",
                "age": 15,
                "validation_info": {"is_valid": True, "checksum_passed": True}
            },
            forensics={"tamper_score": 12.0, "is_flagged": False},
            quality={"quality_score": 85.0, "is_blurry": False},
            face_data={"is_match": True, "face_detected_in_selfie": True, "similarity_score": 88.0},
            duplicate_info={"has_duplicate": False},
            custom_rules=self.rules
        )
        self.assertEqual(res["decision"], "REJECTED")
        self.assertIn("UNDERAGE_APPLICANT", res["security_flags"])

    def test_tampered_document_rejected(self):
        res = evaluate_eligibility(
            applicant_name="Vikram Singh",
            applicant_email="vikram@gmail.com",
            declared_dob="2002-01-10",
            declared_college="State Univ",
            extracted_fields={
                "document_type": "AADHAAR_CARD",
                "name": "VIKRAM SINGH",
                "dob": "10/01/2002",
                "age": 24,
                "validation_info": {"is_valid": True}
            },
            forensics={"tamper_score": 78.0, "is_flagged": True, "assessment": "Altered in Adobe Photoshop"},
            quality={"quality_score": 85.0, "is_blurry": False},
            face_data={"is_match": True, "face_detected_in_selfie": True, "similarity_score": 85.0},
            duplicate_info={"has_duplicate": False},
            custom_rules=self.rules
        )
        self.assertEqual(res["decision"], "REJECTED")
        self.assertIn("POTENTIAL_TAMPERING_DETECTED", res["security_flags"])

    def test_duplicate_sybil_rejected(self):
        res = evaluate_eligibility(
            applicant_name="Karan Malhotra",
            applicant_email="karan@gmail.com",
            declared_dob="2004-08-15",
            declared_college="BITS Pilani",
            extracted_fields={
                "document_type": "AADHAAR_CARD",
                "name": "AARAV SHARMA",
                "dob": "15/08/2004",
                "age": 22,
                "validation_info": {"is_valid": True}
            },
            forensics={"tamper_score": 15.0, "is_flagged": False},
            quality={"quality_score": 90.0, "is_blurry": False},
            face_data={"is_match": True, "face_detected_in_selfie": True, "similarity_score": 80.0},
            duplicate_info={
                "has_duplicate": True,
                "duplicate_type": "SYBIL_ID_REUSE",
                "risk_score": 95,
                "message": "Used by Aarav Sharma"
            },
            custom_rules=self.rules
        )
        self.assertEqual(res["decision"], "REJECTED")
        self.assertIn("SYBIL_DUPLICATE_ID", res["security_flags"])

    def test_blurry_document_routed_to_manual_review(self):
        res = evaluate_eligibility(
            applicant_name="Priya Nair",
            applicant_email="priya@nitk.edu.in",
            declared_dob="2003-11-20",
            declared_college="NITK",
            extracted_fields={
                "document_type": "AADHAAR_CARD",
                "name": "PRIYA NAIR",
                "dob": "20/11/2003",
                "age": 23,
                "institution": "NITK",
                "validation_info": {"is_valid": True}
            },
            forensics={"tamper_score": 12.0, "is_flagged": False},
            quality={"quality_score": 35.0, "is_blurry": True, "summary": "Blurry image"},
            face_data={"is_match": True, "face_detected_in_selfie": True, "similarity_score": 75.0},
            duplicate_info={"has_duplicate": False},
            custom_rules=self.rules
        )
        # Should NOT hard reject legitimate participant for a blurry photo; route to manual triage!
        self.assertEqual(res["decision"], "MANUAL_REVIEW")

if __name__ == "__main__":
    unittest.main()
