import unittest
from backend.ocr.checksums import (
    compute_verhoeff_checksum,
    validate_aadhaar_checksum,
    validate_aadhaar,
    validate_pan,
    validate_college_id
)

class TestChecksums(unittest.TestCase):
    def test_verhoeff_checksum(self):
        # 11 digits: 98432109876
        check = compute_verhoeff_checksum("98432109876")
        full = f"98432109876{check}"
        self.assertTrue(validate_aadhaar_checksum(full))

        # Corrupted last digit should fail
        corrupted = f"98432109876{(check + 1) % 10}"
        self.assertFalse(validate_aadhaar_checksum(corrupted))

    def test_validate_aadhaar(self):
        check = compute_verhoeff_checksum("98432109876")
        res = validate_aadhaar(f"9843 2109 876{check}")
        self.assertTrue(res["is_valid"])
        self.assertTrue(res["checksum_passed"])

        # Masked Aadhaar
        res_masked = validate_aadhaar("XXXX XXXX 1234")
        self.assertTrue(res_masked["is_valid"])
        self.assertTrue(res_masked["is_masked"])

    def test_validate_pan(self):
        # Valid individual PAN (4th character 'P' for person)
        valid_pan = "ABCPE1234F"
        res = validate_pan(valid_pan)
        self.assertTrue(res["is_valid"])
        self.assertTrue(res["is_individual"])

        # Invalid structure
        invalid_pan = "12345ABCDE"
        res_inv = validate_pan(invalid_pan)
        self.assertFalse(res_inv["is_valid"])

    def test_validate_college_id(self):
        res = validate_college_id("21BCE1042")
        self.assertTrue(res["is_valid"])

        res_short = validate_college_id("A")
        self.assertFalse(res_short["is_valid"])

if __name__ == "__main__":
    unittest.main()
