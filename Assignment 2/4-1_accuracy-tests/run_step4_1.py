"""Run both frozen confidence cascades on the held-out accuracy tickets."""
import csv
from contextlib import contextmanager
import json
import os
from pathlib import Path
from statistics import median
import subprocess
import sys
import time
from types import SimpleNamespace

import requests

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parent
sys.path.insert(0, str(ROOT))

from accuracy import (FIELDS, accuracy_metrics, attach_escalations, classify_for_accuracy,
                      compare_reports, read_logs, save_json, split_labels, subset_predictions)
from benchmark import warmup
from data_tools import source_rows, verify_formal_inputs
from model_config import MODEL_DIGESTS
from single_model_benchmark import OLLAMA_URL, TOP_MODEL, new_run_id

SMALL = "llama3.2:3b"
REFERENCE = ROOT / "1_accuracy-limits/results/step1-20261127T140752Z-14aa0cd1/test/qwen-7b"
SETTINGS = [(1, 90), (2, 80)]


@contextmanager
def benchmark_api(run_id, setting, threshold, logs):
    # An isolated API and SQLite database per setting preserve the existing service.
    env = dict(os.environ, MODE="cascade", MODEL_NAME=SMALL, MODEL_DIGEST=MODEL_DIGESTS[SMALL],
               LARGE_MODEL=TOP_MODEL, LARGE_MODEL_DIGEST=MODEL_DIGESTS[TOP_MODEL], CASCADE_SETTING=str(setting),
               CONFIDENCE_THRESHOLD=str(threshold), ACCEPT_CATEGORIES="", RUN_ID=run_id,
               TRIAGE_LOG_DIR=logs.as_posix(), MODEL_TIMEOUT="600")
    name = f"ict3113-a2-{run_id}"
    subprocess.run(["docker", "compose", "run", "--detach", "--rm", "--no-deps", "--name", name,
                    "--publish", "127.0.0.1::8000", "api"], env=env, cwd=ROOT, check=True)
    try:
        binding = subprocess.check_output(["docker", "port", name, "8000/tcp"], text=True).strip()
        url = f"http://{binding}"
        expected = {"X-Run-ID": run_id, "X-Model-Digest": MODEL_DIGESTS[SMALL], "X-Large-Model": TOP_MODEL,
                    "X-Cascade-Setting": str(setting), "X-Confidence-Threshold": str(threshold)}
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            try:
                response = requests.get(url + "/stats", timeout=3)
            except requests.ConnectionError:
                time.sleep(1)
                continue
            response.raise_for_status()
            if any(response.headers.get(k) != v for k, v in expected.items()):
                raise ValueError("Unexpected benchmark API configuration")
            yield url
            return
        raise RuntimeError("Timed out waiting for the benchmark API")
    finally:
        subprocess.run(["docker", "stop", name], check=True)


def measure(url, run_id, narratives, labels, result_dir):
    records = []
    started = time.perf_counter()
    with (result_dir / "predictions.csv").open("x", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for row, actual in sorted(labels.items()):
            record = classify_for_accuracy(url, SMALL, run_id, row, narratives[row], actual, timeout=1850)
            writer.writerow(record)
            file.flush()
            records.append(record)
            print(f"{run_id} {len(records)}/{len(labels)} row={row} status={record['status']} "
                  f"elapsed={record['elapsed_ms'] / 1000:.2f}s", flush=True)
    return records, time.perf_counter() - started


def summarize(records, elapsed, narratives, run_id, setting, threshold, logs, result_dir):
    audits = read_logs(logs / f"{run_id}.jsonl")
    if set(audits) != {record["request_id"] for record in records}:
        raise ValueError("Mismatch between measured requests and service audit")
    attach_escalations(records, audits)
    with (logs / f"{run_id}.tickets.jsonl").open("x", encoding="utf-8") as file:
        for record in records:
            audit = audits[record["request_id"]]
            score = audit["confidence"]
            if (audit["run_id"] != run_id or audit["cascade_setting"] != str(setting)
                    or audit["confidence_threshold"] != threshold or audit["large_model_digest"] != MODEL_DIGESTS[TOP_MODEL]):
                raise ValueError(f"Wrong configuration at row {record['row']}")
            if record["predicted_category"] != "ERROR":
                escalated = score is None or score < threshold
                expected = [(SMALL, "category")]
                if audit["small_model_prediction"] != "ERROR":
                    expected.append((SMALL, "confidence"))
                if escalated:
                    expected.append((TOP_MODEL, "category"))
                actual = [(c["model"], c["purpose"]) for c in audit["model_calls"]]
                if (actual != expected or record["escalated"] != escalated
                        or record["final_model"] != expected[-1][0]):
                    raise ValueError(f"Invalid route or calls at row {record['row']}")
            details = {**audit, **record, "narrative": narratives[record["row"]],
                       "correct": record["actual_category"] == record["predicted_category"]}
            file.write(json.dumps(details, ensure_ascii=False) + "\n")
    report = accuracy_metrics(records)
    report.update(split="test", run_id=run_id, mode="cascade", setting=setting, confidence_threshold=threshold,
                  model=SMALL, large_model=TOP_MODEL, model_digests={m: MODEL_DIGESTS[m] for m in (SMALL, TOP_MODEL)},
                  confidence_errors=sum(bool(a["confidence_error"]) for a in audits.values()),
                  wall_seconds=elapsed, median_ticket_ms=median(r["elapsed_ms"] for r in records),
                  sum_ticket_ms=sum(r["elapsed_ms"] for r in records))
    path = result_dir / "accuracy.json"
    save_json(path, report)
    return path


def main():
    verify_formal_inputs()
    reference = json.loads((REFERENCE / "accuracy.json").read_text(encoding="utf-8"))
    saved = subset_predictions(REFERENCE / "predictions.csv", "test")
    if (reference["model"] != TOP_MODEL or reference["digest"] != MODEL_DIGESTS[TOP_MODEL]
            or reference["split"] != "test" or reference["mode"] != "single"
            or accuracy_metrics(saved)["per_category"] != reference["per_category"]):
        raise ValueError("The Step 1 reference does not match its held-out predictions")
    narratives, labels = source_rows(), split_labels("test")
    batch = new_run_id("step4")
    results = STAGE / "results" / batch
    print(f"Accuracy batch: {batch}", flush=True)
    subprocess.run(["docker", "compose", "up", "-d", "--wait", "ollama"], cwd=ROOT, check=True)
    subprocess.run(["docker", "compose", "build", "api"], cwd=ROOT, check=True)
    reports = []
    for setting, threshold in SETTINGS:
        name = f"setting-{setting}-{threshold}"
        run_id = f"{batch}-{name}"
        result_dir = results / name
        logs = STAGE / "logs" / batch / name
        result_dir.mkdir(parents=True, exist_ok=False)
        logs.mkdir(parents=True, exist_ok=False)
        with benchmark_api(run_id, setting, threshold, logs) as url:
            warmup(SimpleNamespace(model=[SMALL, TOP_MODEL], ollama=OLLAMA_URL, timeout=600,
                                   output=result_dir / "residency.json"))
            records, elapsed = measure(url, run_id, narratives, labels, result_dir)
        path = summarize(records, elapsed, narratives, run_id, setting, threshold, logs, result_dir)
        reports.append((name, path))
        print(f"Completed {name}: {path}", flush=True)
    comparison = compare_reports(REFERENCE / "accuracy.json", reports)
    comparison["reference_path"] = REFERENCE.relative_to(ROOT).as_posix() + "/accuracy.json"
    save_json(results / "comparison.json", comparison)
    for outcome in comparison["configurations"]:
        print(outcome["configuration"], outcome["accuracy"]["overall"], "qualifies:", outcome["qualifies"], flush=True)


if __name__ == "__main__":
    main()
