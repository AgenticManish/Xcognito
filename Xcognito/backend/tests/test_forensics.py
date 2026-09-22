import unittest
from backend.data.sample_generator import create_sample_aadhaar
from backend.forensics.tampering_detector import analyze_document_tampering
from backend.forensics.quality_analyzer import evaluate_document_quality

class TestForensics(unittest.TestCase):
    def test_tampering_detection(self):
        # 1. Clean image
        clean_bytes = create_sample_aadhaar(tamper_dob=False)
        clean_res = analyze_document_tampering(clean_bytes)
        self.assertIn("tamper_score", clean_res)
        self.assertIsNotNone(clean_res["ela_heatmap_url"])

        # 2. Photoshopped / Tampered image
        tampered_bytes = create_sample_aadhaar(tamper_dob=True)
        tampered_res = analyze_document_tampering(tampered_bytes)
        
        # The tampered image should register higher tamper variance than the clean one
        self.assertGreater(tampered_res["tamper_score"], clean_res["tamper_score"])

    def test_quality_analysis(self):
        # Sharp image
        sharp_bytes = create_sample_aadhaar(is_blurry=False)
        sharp_res = evaluate_document_quality(sharp_bytes)
        self.assertFalse(sharp_res["is_blurry"])
        self.assertGreater(sharp_res["laplacian_variance"], 50.0)

        # Blurry image
        blurry_bytes = create_sample_aadhaar(is_blurry=True)
        blurry_res = evaluate_document_quality(blurry_bytes)
        self.assertTrue(blurry_res["is_blurry"])
        self.assertLess(blurry_res["laplacian_variance"], sharp_res["laplacian_variance"])

if __name__ == "__main__":
    unittest.main()
