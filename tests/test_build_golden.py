from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from build_golden import build_golden
from dataset import read_csv, write_csv


class GoldenTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.a = self.path / "a.csv"
        self.b = self.path / "b.csv"
        self.resolutions = self.path / "resolutions.csv"
        self.output = self.path / "golden.csv"
        self.rows = [{"row": n, "category": "Mortgage"} for n in range(11000, 11175)]
        write_csv(self.a, ["row", "category"], self.rows)
        write_csv(self.b, ["row", "category"], reversed(self.rows))
        patcher = patch("build_golden.team_rows", return_value=set(range(11000, 12000)))
        patcher.start()
        self.addCleanup(patcher.stop)

    def decide(self, **overrides):
        record = {"row": 11000, "category_a1": "Mortgage", "category_a2": "Credit card",
                  "resolved_category": "Consumer loan", "resolution_reason": "Team discussion: complaint concerns a personal loan."}
        record.update(overrides)
        write_csv(self.resolutions, list(record), [record])

    def dispute(self):
        self.rows[0]["category"] = "Credit card"
        write_csv(self.b, ["row", "category"], self.rows)

    def test_agreements_join_by_id_and_existing_file_is_protected(self):
        report = build_golden(self.a, self.b, None, self.output)
        self.assertEqual(report["agreements"], 175)
        self.assertEqual(len(read_csv(self.output, ["row", "category"])), 175)
        with self.assertRaises(FileExistsError):
            build_golden(self.a, self.b, None, self.output)

    def test_recorded_resolution_can_choose_a_third_category(self):
        self.dispute()
        self.decide()
        report = build_golden(self.a, self.b, self.resolutions, self.output)
        self.assertEqual(report["human_resolutions"], 1)
        self.assertEqual(read_csv(self.output, ["row", "category"])[0]["category"], "Consumer loan")

    def test_missing_resolution_never_writes_output(self):
        self.dispute()
        with self.assertRaisesRegex(ValueError, "unresolved"):
            build_golden(self.a, self.b, None, self.output)
        self.assertFalse(self.output.exists())

    def test_blank_invalid_stale_and_unexpected_resolutions_rejected(self):
        self.dispute()
        for fields in ({"resolution_reason": " "}, {"resolved_category": ""},
                       {"resolved_category": "Unknown"}, {"category_a1": "Debt collection"},
                       {"row": 11001}):
            with self.subTest(fields=fields):
                self.decide(**fields)
                with self.assertRaises(ValueError):
                    build_golden(self.a, self.b, self.resolutions, self.output)
                self.assertFalse(self.output.exists())

    def test_duplicate_resolutions_rejected(self):
        self.dispute()
        self.decide()
        rows = read_csv(self.resolutions, ["row"])
        write_csv(self.resolutions, list(rows[0]), rows * 2)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            build_golden(self.a, self.b, self.resolutions, self.output)

    def test_mismatched_annotator_sets_rejected(self):
        write_csv(self.b, ["row", "category"], self.rows[1:])
        with self.assertRaisesRegex(ValueError, "same rows"):
            build_golden(self.a, self.b, None, self.output)
