
import unittest
from source_guard import validate_report


class TestSourceGuard(unittest.TestCase):

    def setUp(self):
        self.trusted = {"10.1097/00001756-200011270-00046"}

    def test_valid_doi(self):
        report = (
            "研究 DOI: "
            "10.1097/00001756-200011270-00046"
        )
        ok, _ = validate_report(report, self.trusted)
        self.assertTrue(ok)

    def test_unknown_doi(self):
        report = "研究 DOI: 10.1234/fake-paper"
        ok, _ = validate_report(report, self.trusted)
        self.assertFalse(ok)

    def test_missing_doi(self):
        report = "这是一份没有提供DOI的研究报告。"
        ok, _ = validate_report(report, self.trusted)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
