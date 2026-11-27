"""Measure a pinned A1 model on a frozen split and record its confidence."""
import csv
from datetime import datetime, timezone
import json
import subprocess
import sys
import time
import uuid

import requests

from accuracy import (FIELDS, accuracy_floors, accuracy_metrics, classify_for_accuracy,
                      save_json, split_labels, verify_service)
from data_tools import ROOT, source_rows
from model_config import MODEL_DIGESTS, confidence_payload, parse_confidence

TOP_MODEL = "qwen2.5:7b"
SERVICE_URL = "http://127.0.0.1:8000"
OLLAMA_URL = "http://127.0.0.1:11434"


def ask_confidence(ollama_url, model, narrative, prediction):
    response = requests.post(ollama_url + "/api/generate",
                             json=confidence_payload(model, narrative, prediction), timeout=600)
    response.raise_for_status()
    generation = response.json()
    if generation["model"] != model:
        raise ValueError("Confidence response came from an unexpected model")
    return parse_confidence(generation["response"])


def measure(model, run_id, result_dir, ticket_log, *, split="test"):
    verify_service(SERVICE_URL, model, run_id)
    narratives = source_rows()
    labels = split_labels(split)
    records = []
    with ticket_log.open("x", encoding="utf-8") as log, (result_dir / "predictions.csv").open(
            "x", encoding="utf-8", newline="") as predictions:
        writer = csv.DictWriter(predictions, fieldnames=[*FIELDS, "confidence", "confidence_elapsed_ms", "confidence_error"])
        writer.writeheader()
        for index, (row, actual) in enumerate(sorted(labels.items()), 1):
            narrative = narratives[row]
            record = classify_for_accuracy(SERVICE_URL, model, run_id, row, narrative, actual, timeout=1300)
            record.update(confidence=None, confidence_elapsed_ms=None, confidence_error="")
            if record["predicted_category"] != "ERROR":
                start = time.perf_counter()
                try:
                    record["confidence"] = ask_confidence(OLLAMA_URL, model, narrative, record["predicted_category"])
                except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
                    record["confidence_error"] = str(exc)
                record["confidence_elapsed_ms"] = round((time.perf_counter() - start) * 1000, 3)
            audit = {"run_id": run_id, "model": model, "narrative": narrative, **record}
            log.write(json.dumps(audit, ensure_ascii=False) + "\n")
            log.flush()
            writer.writerow(record)
            predictions.flush()
            records.append(record)
            print(f"{index}/{len(labels)} row={row} predicted={record['predicted_category']} "
                  f"confidence={record['confidence']}", flush=True)

    report = accuracy_metrics(records)
    report.update(split=split, mode="single", model=model, digest=MODEL_DIGESTS[model], run_id=run_id,
                  tickets_with_confidence=sum(r["confidence"] is not None for r in records),
                  confidence_errors=sum(bool(r["confidence_error"]) for r in records))
    if model == TOP_MODEL and split == "test":
        report["accuracy_floors_pct"] = accuracy_floors(report)
    save_json(result_dir / "accuracy.json", report)
    return report


def new_run_id(prefix):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}-{stamp}-{uuid.uuid4().hex[:8]}"


def run_single_model(model, run_id, result_dir, log_dir, *, split="test"):
    log_dir.mkdir(parents=True, exist_ok=False)
    subprocess.run([sys.executable, str(ROOT / "start_config.py"), "--model", model,
                    "--run-id", run_id, "--log-dir", str(log_dir)], check=True)
    result_dir.mkdir(parents=True, exist_ok=False)
    ticket_log = log_dir / f"{run_id}.tickets.jsonl"
    print(f"Results: {result_dir}\nTicket log: {ticket_log}", flush=True)
    report = measure(model, run_id, result_dir, ticket_log, split=split)
    overall = report["overall"]
    print(f"{model} classified {overall['correct']}/{overall['count']} correctly "
          f"({overall['accuracy_pct']:.2f}%). Confidence scores: "
          f"{report['tickets_with_confidence']}/{overall['count']}.")
    return result_dir / "accuracy.json"
