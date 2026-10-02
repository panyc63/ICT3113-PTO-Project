import base64
from contextlib import closing
import csv
import json
import logging
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

# Isolated disposable database/logs; unit checks must not look like benchmarks.
TEMP = tempfile.TemporaryDirectory()
os.environ.update(DB_PATH=str(Path(TEMP.name) / "tickets.db"),
                  LOG_PATH=str(Path(TEMP.name) / "audit.jsonl"),
                  RUN_ID="development", MODEL_DIGEST="")
from fastapi.testclient import TestClient
import requests
import main
from categories import CATEGORIES
from dataset import DEFAULT_DATASET, label_rows, read_csv, team_rows, write_csv
from prepare_data import prepare
from calculate_agreement import evaluate_agreement
from evaluate_accuracy import accuracy_metrics


class ServiceTests(unittest.TestCase):
    def setUp(self):
        main.init_db()
        with closing(main.get_db()) as conn, conn:
            conn.execute("DELETE FROM tickets")
        self.client_context = TestClient(main.app, raise_server_exceptions=False)
        self.client = self.client_context.__enter__()

    def tearDown(self):
        self.client_context.__exit__(None, None, None)

    def test_empty_then_post_search_and_stats(self):
        self.assertEqual(self.client.get("/stats").json(), dict.fromkeys(CATEGORIES, 0))
        response = Mock()
        response.json.return_value = {"response": "Mortgage", "eval_count": 4}
        with patch("main.requests.post", return_value=response) as post:
            saved = self.client.post("/tickets", json={"narrative": "Mortgage complaint\nsecond line"},
                                     headers={"X-Request-ID": "test-post", "X-Source-Row": "11000"})
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.json()["category"], "Mortgage")
        self.assertEqual(post.call_args.kwargs["json"]["options"]["num_gpu"], 0)
        self.assertFalse(post.call_args.kwargs["json"]["stream"])
        self.assertEqual(len(self.client.get("/search", params={"q": "Mortgage"}).json()), 1)
        self.assertEqual(self.client.get("/stats").json()["Mortgage"], 1)
        self.assertEqual(saved.headers["X-Request-ID"], "test-post")

    def test_bad_backend_output_is_not_fake_credit_reporting(self):
        for payload in ({"response": "Credit reporting or Mortgage"}, {"error": "missing model"},
                        {"response": None}, []):
            with self.subTest(payload=payload):
                response = Mock()
                response.json.return_value = payload
                with patch("main.requests.post", return_value=response):
                    self.assertEqual(self.client.post("/tickets", json={"narrative": "text"}).status_code, 502)
        self.assertEqual(sum(self.client.get("/stats").json().values()), 0)

    def test_upstream_http_failure_and_timeout(self):
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("500")
        with patch("main.requests.post", return_value=response):
            self.assertEqual(self.client.post("/tickets", json={"narrative": "text"}).status_code, 502)
        with patch("main.requests.post", side_effect=requests.Timeout):
            self.assertEqual(self.client.post("/tickets", json={"narrative": "text"}).status_code, 504)

    def test_all_request_paths_and_failures_are_logged(self):
        for method, path, kwargs in [
            ("GET", "/stats", {}), ("GET", "/search?q=test", {}),
            ("GET", "/search", {}), ("GET", "/missing", {}),
            ("POST", "/tickets", {"json": {"narrative": "  "}}),
            ("POST", "/tickets", {"content": "broken JSON"}),
        ]:
            request_id = f"audit-{method}-{path}-{len(kwargs)}"
            response = self.client.request(method, path, headers={"X-Request-ID": request_id}, **kwargs)
            records = [json.loads(line) for line in main.LOG_PATH.read_text().splitlines()]
            record = next(r for r in reversed(records) if r["request_id"] == request_id)
            self.assertEqual(record["status"], response.status_code)
            self.assertGreaterEqual(record["duration_ms"], 0)

    def test_internal_failure_is_logged(self):
        with patch("main.get_db", side_effect=RuntimeError("test failure")):
            self.assertEqual(self.client.get("/stats", headers={"X-Request-ID": "internal-error"}).status_code, 500)
        records = [json.loads(line) for line in main.LOG_PATH.read_text().splitlines()]
        self.assertEqual(records[-1]["error"], "RuntimeError")

    def test_pin_mismatch_blocks_startup(self):
        response = Mock()
        response.json.return_value = {"models": [{"name": main.MODEL_NAME, "digest": "actual"}]}
        with patch.object(main, "MODEL_DIGEST", "expected"), patch("main.requests.get", return_value=response):
            with self.assertRaises(RuntimeError):
                with TestClient(main.app):
                    pass


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = team_rows()

    def test_exact_team_range(self):
        self.assertEqual(set(self.source), set(range(11000, 12000)))

    def test_generated_traffic_round_trips_all_original_narratives(self):
        traffic = read_csv("data/team11/jmeter_tickets.csv", ("row", "payload_b64"))
        self.assertEqual(len(traffic), 1000)
        self.assertEqual({int(r["row"]) for r in traffic}, set(self.source))
        for item in traffic:
            payload = json.loads(base64.b64decode(item["payload_b64"]).decode("utf-8"))
            self.assertEqual(payload, {"narrative": self.source[int(item["row"])]["narrative"]})

    def test_blind_label_sheets_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "prepared"
            prepare(DEFAULT_DATASET, 11, output)
            first = read_csv(output / "labels_member1.csv", ("row", "narrative", "category"))
            second = read_csv(output / "labels_member2.csv", ("row", "narrative", "category"))
            self.assertEqual(first, second)
            self.assertEqual(len(first), 175)
            self.assertTrue(all(r["category"] == "" and "source_label" not in r for r in first))
            with self.assertRaises(FileExistsError):
                prepare(DEFAULT_DATASET, 11, output)

    def test_reject_noisy_raw_labels_and_incomplete_sheets(self):
        with self.assertRaises(ValueError):
            label_rows(DEFAULT_DATASET, self.source)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "blank.csv"
            write_csv(path, ["row", "category"], [{"row": 11000, "category": ""}])
            with self.assertRaises(ValueError):
                label_rows(path, self.source)

    def test_agreement_matches_by_row_and_rejects_missing_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            labels = [{"row": row, "category": CATEGORIES[row % 7]} for row in range(11000, 11175)]
            other = [dict(row) for row in reversed(labels)]
            other[0]["category"] = CATEGORIES[(other[0]["row"] + 1) % 7]
            write_csv(path / "a.csv", ["row", "category"], labels)
            write_csv(path / "b.csv", ["row", "category"], other)
            report = evaluate_agreement(path / "a.csv", path / "b.csv", output=path / "out")
            self.assertEqual(report["disagreements"], 1)
            self.assertAlmostEqual(report["raw_agreement"], 174 / 175)
            self.assertAlmostEqual(report["cohen_kappa"], (174 / 175 - 1 / 7) / (1 - 1 / 7))
            write_csv(path / "b.csv", ["row", "category"], other[1:])
            with self.assertRaises(ValueError):
                evaluate_agreement(path / "a.csv", path / "b.csv", output=path / "missing")

    def test_duplicate_and_out_of_team_labels_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "labels.csv"
            for rows in ([{"row": 11000, "category": "Mortgage"}] * 175,
                         [{"row": 10000, "category": "Mortgage"}]):
                write_csv(path, ["row", "category"], rows)
                with self.assertRaises(ValueError):
                    label_rows(path, self.source)

    def test_accuracy_keeps_errors_in_denominator(self):
        report = accuracy_metrics([
            {"actual_category": "Mortgage", "predicted_category": "Mortgage"},
            {"actual_category": "Mortgage", "predicted_category": "ERROR"},
            {"actual_category": "Credit card", "predicted_category": "Mortgage"},
        ])
        self.assertEqual(report["overall_accuracy"], 1 / 3)
        self.assertEqual(report["per_category"]["Mortgage"]["accuracy_recall"], 0.5)
        self.assertEqual(report["error_count"], 1)
        self.assertIsNone(report["per_category"]["Consumer loan"]["accuracy_recall"])


def tearDownModule():
    for handler in main.logger.handlers[:]:
        handler.close()
        main.logger.removeHandler(handler)
    TEMP.cleanup()


if __name__ == "__main__":
    unittest.main()
