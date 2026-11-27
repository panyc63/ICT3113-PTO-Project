"""Regression checks for the confidence cutoffs and fallback paths without Ollama."""
import importlib
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
SMALL, LARGE = "llama3.2:3b", "qwen2.5:7b"


class ConfidenceCascadeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        audit_path = Path(cls.temp.name) / "audit.jsonl"
        with patch.dict(os.environ, LOG_PATH=str(audit_path)):
            cls.api = importlib.import_module("main")
        for handler in cls.api.logger.handlers:
            if Path(handler.baseFilename) == audit_path:
                cls.addClassCleanup(handler.close)
                cls.addClassCleanup(cls.api.logger.removeHandler, handler)

    def route(self, cutoff, confidence, *, mode="cascade", invalid_category=False, accepted=()):
        request = SimpleNamespace(state=SimpleNamespace())
        small_answer = "invalid" if invalid_category else json.dumps({"category": "Mortgage"})

        def generate(url, json, timeout):
            if json["model"] == LARGE:
                answer = '{"category":"Credit card"}'
            elif "confidence" in json["format"]["properties"]:
                if isinstance(confidence, Exception):
                    raise confidence
                answer = confidence
            else:
                answer = small_answer
            return Mock(json=lambda: {"response": answer, "model": json["model"]})

        with patch.multiple(self.api, MODE=mode, MODEL_NAME=SMALL, LARGE_MODEL=LARGE,
                            CONFIDENCE_THRESHOLD=cutoff, ACCEPTED=set(accepted),
                            DB_PATH=Path(self.temp.name) / "tickets.db"), patch.object(self.api.requests, "post", generate):
            self.api.init_db()
            result = self.api.classify_ticket(self.api.TicketRequest(narrative="test ticket"), request)
        return result["category"], request.state

    def test_threshold_boundaries(self):
        for cutoff in (80, 90):
            for score in (79, 80, 89, 90):
                with self.subTest(cutoff=cutoff, score=score):
                    category, state = self.route(cutoff, json.dumps({"confidence": score}))
                    self.assertEqual(category, "Mortgage" if score >= cutoff else "Credit card")
                    self.assertEqual(state.confidence, score)
                    self.assertEqual(state.escalated, score < cutoff)
                    calls = [(c["model"], c["purpose"]) for c in state.model_calls]
                    expected = [(SMALL, "category"), (SMALL, "confidence")]
                    self.assertEqual(calls, expected + ([(LARGE, "category")] if score < cutoff else []))
                    self.assertTrue(all(c["duration_ms"] >= 0 for c in state.model_calls))

    def test_unavailable_confidence_escalates(self):
        for answer in ('{}', '{"confidence":true}', '{"confidence":101}', self.api.requests.Timeout()):
            with self.subTest(answer=answer):
                category, state = self.route(80, answer)
                self.assertEqual(category, "Credit card")
                self.assertEqual(state.escalation_reason, "confidence_unavailable")
                self.assertTrue(state.confidence_error)
                self.assertEqual(len(state.model_calls), 3)

    def test_invalid_small_category_goes_directly_to_qwen(self):
        category, state = self.route(90, None, invalid_category=True)
        self.assertEqual(category, "Credit card")
        self.assertEqual(state.escalation_reason, "invalid_small_output")
        self.assertEqual([c["purpose"] for c in state.model_calls], ["category", "category"])

    def test_existing_single_model_and_category_routes(self):
        for mode, accepted, expected in (("single", (), "Mortgage"), ("cascade", ["Mortgage"], "Mortgage"),
                                         ("cascade", (), "Credit card")):
            with self.subTest(mode=mode, accepted=accepted):
                category, state = self.route(None, None, mode=mode, accepted=accepted)
                self.assertEqual(category, expected)
                self.assertTrue(all(c["purpose"] == "category" for c in state.model_calls))


if __name__ == "__main__":
    unittest.main()
