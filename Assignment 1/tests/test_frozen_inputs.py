from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from evaluate_accuracy import committed_file


class FrozenInputTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.path = self.root / "golden.csv"
        self.path.write_bytes(b"row,category\n11000,Mortgage\n")

    def test_uncommitted_input_has_actionable_message(self):
        with patch("evaluate_accuracy.subprocess.check_output", side_effect=[
            str(self.root), subprocess.CalledProcessError(128, ["git", "show"]),
        ]):
            with self.assertRaisesRegex(ValueError, "Finish and commit both"):
                committed_file(self.path)

    def test_missing_file_explains_what_to_create(self):
        with self.assertRaisesRegex(ValueError, "Input file does not exist"):
            committed_file(self.root / "predictions.md")

    def test_changed_input_still_blocked(self):
        with patch("evaluate_accuracy.subprocess.check_output", side_effect=[str(self.root), b"old content"]):
            with self.assertRaisesRegex(ValueError, "Commit the final version"):
                committed_file(self.path)

    def test_committed_input_accepts_windows_line_endings(self):
        committed = self.path.read_bytes().replace(b"\n", b"\r\n")
        with patch("evaluate_accuracy.subprocess.check_output", side_effect=[str(self.root), committed]):
            self.assertEqual(len(committed_file(self.path)), 64)

    def test_outside_repository_rejected(self):
        with patch("evaluate_accuracy.subprocess.check_output", return_value=str(self.root / "other")):
            with self.assertRaisesRegex(ValueError, "inside the project Git repository"):
                committed_file(self.path)

    def test_missing_repository_has_actionable_message(self):
        with patch("evaluate_accuracy.subprocess.check_output", side_effect=subprocess.CalledProcessError(128, ["git"])):
            with self.assertRaisesRegex(ValueError, "Run accuracy evaluation from inside"):
                committed_file(self.path)
