
import unittest
from arxiv_guard import validate_arxiv_report


class TestArxivGuard(unittest.TestCase):

    def setUp(self):
        self.urls = [
            "https://arxiv.org/abs/2610.13889v1"
        ]

    def test_valid_source(self):
        report = "参考：https://arxiv.org/abs/2610.13889"
        ok, _ = validate_arxiv_report(report, self.urls)
        self.assertTrue(ok)

    def test_unknown_source(self):
        report = "参考：https://arxiv.org/abs/2610.99999"
        ok, _ = validate_arxiv_report(report, self.urls)
        self.assertFalse(ok)

    def test_missing_source(self):
        report = "最近有一项重要的AI研究。"
        ok, _ = validate_arxiv_report(report, self.urls)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
