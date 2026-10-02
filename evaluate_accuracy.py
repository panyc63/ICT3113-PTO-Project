"""Evaluate frozen human labels against narratives taken from the original CSV."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import time
import uuid
import requests
from categories import CATEGORIES
from dataset import DEFAULT_DATASET, DEFAULT_TEAM, label_rows, team_rows


def committed_file(path):
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError(f"Input file does not exist: {path}. Create it before running accuracy evaluation")
    try:
        root = Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.PIPE,
        ).strip()).resolve()
    except subprocess.CalledProcessError as exc:
        raise ValueError("Run accuracy evaluation from inside the project Git repository") from exc
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError(f"Input must be inside the project Git repository: {path}") from exc
    try:
        committed = subprocess.check_output(
            ["git", "show", f"HEAD:{relative}"], stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        raise ValueError(
            f"Cannot read {relative} from the latest Git commit (HEAD). "
            "The file may exist locally but has not been committed. "
            "Finish and commit both the golden set and prediction record before benchmarking"
        ) from exc
    current = path.read_bytes()
    if committed.replace(b"\r\n", b"\n") != current.replace(b"\r\n", b"\n"):
        raise ValueError(f"Commit the final version of {relative} before benchmarking")
    return hashlib.sha256(current).hexdigest()


def accuracy_metrics(records):
    labels = CATEGORIES + ["ERROR"]
    matrix = {actual: {predicted: 0 for predicted in labels} for actual in CATEGORIES}
    for record in records:
        matrix[record["actual_category"]][record["predicted_category"]] += 1
    correct = sum(matrix[cat][cat] for cat in CATEGORIES)
    count = len(records)
    return {
        "count": count, "overall_accuracy": correct / count if count else None,
        "error_count": sum(matrix[cat]["ERROR"] for cat in CATEGORIES),
        "per_category": {
            cat: {"support": sum(matrix[cat].values()),
                  "accuracy_recall": matrix[cat][cat] / sum(matrix[cat].values())
                  if sum(matrix[cat].values()) else None}
            for cat in CATEGORIES
        },
        "confusion_matrix": matrix,
        "confusion_matrix_orientation": "rows=human label, columns=prediction; errors count as incorrect",
    }


def run_accuracy_test(golden_csv_path, target_url, prediction_record, model, digest, run_id,
                      output, dataset=DEFAULT_DATASET, team=DEFAULT_TEAM, timeout=130):
    source = team_rows(dataset, team)
    golden = label_rows(golden_csv_path, source)
    golden_hash = committed_file(golden_csv_path)
    predictions_hash = committed_file(prediction_record)
    if not digest or run_id == "development":
        raise ValueError("Use a pinned model digest and a unique reported run ID")
    # Check identity before any golden narrative reaches a model.
    probe = requests.get(target_url.removesuffix("/tickets") + "/stats", timeout=10)
    probe.raise_for_status()
    expected = {"X-Model-Name": model, "X-Model-Digest": digest, "X-Run-ID": run_id}
    if any(probe.headers.get(k) != v for k, v in expected.items()):
        raise ValueError("Service model/digest/run ID does not match this accuracy run")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    metadata = {"model": model, "digest": digest, "run_id": run_id, "team": team,
                "golden_sha256": golden_hash, "prediction_record_sha256": predictions_hash,
                "dataset_sha256": hashlib.sha256(Path(dataset).read_bytes()).hexdigest(),
                "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()}
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    records = []
    with (output / "predictions.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["row", "request_id", "actual_category", "predicted_category", "status", "elapsed_ms", "error"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row, actual in sorted(golden.items()):
            request_id = str(uuid.uuid4())
            started = time.perf_counter()
            predicted, status, error = "ERROR", 0, ""
            try:
                response = requests.post(target_url, json={"narrative": source[row]["narrative"]},
                    headers={"X-Request-ID": request_id, "X-Source-Row": str(row)}, timeout=timeout)
                status = response.status_code
                response.raise_for_status()
                if any(response.headers.get(k) != v for k, v in expected.items()):
                    raise ValueError("Service identity changed during run")
                category = response.json()["category"]
                if category not in CATEGORIES:
                    raise ValueError("Invalid prediction")
                predicted = category
            except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
                error = str(exc)
            record = dict(zip(fields, [row, request_id, actual, predicted, status,
                                     round((time.perf_counter() - started) * 1000, 3), error]))
            records.append(record)
            writer.writerow(record)
            handle.flush()
    report = accuracy_metrics(records)
    (output / "accuracy.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("golden_csv_path", help="Human-adjudicated CSV with row,category columns")
    parser.add_argument("--target-url", required=True, help="http://SUT-IP:8000/tickets")
    parser.add_argument("--prediction-record", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--digest", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--team", type=int, default=DEFAULT_TEAM)
    parser.add_argument("--timeout", type=float, default=130)
    args = parser.parse_args()
    try:
        report = run_accuracy_test(**vars(args))
    except (ValueError, OSError, subprocess.CalledProcessError, requests.RequestException) as exc:
        parser.exit(1, f"Cannot run accuracy evaluation: {exc}\n")
    print(json.dumps(report, indent=2))
