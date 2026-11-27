"""Assignment 2 accuracy runner, tuning-only analysis, and held-out comparisons."""
import argparse
import json
from pathlib import Path
import time
import uuid
from collections import Counter

import requests

from categories import CATEGORIES
from data_tools import (DATA, ROOT, labels, read_csv, verify_split, verify_formal_inputs,
                        source_rows, write_csv)
from model_config import MODEL_DIGESTS, accept_categories, should_escalate

FIELDS = ["row", "request_id", "actual_category", "predicted_category", "status", "elapsed_ms", "error"]


def save_json(path, value):
    with Path(path).open("x", encoding="utf-8") as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write("\n")


def split_labels(split):
    return labels(DATA / f"golden_{split}.csv")


def subset_predictions(path, split):
    expected = split_labels(split)
    relevant = {}
    for record in read_csv(path):
        row = int(record["row"])
        if row not in expected:
            continue  # Never use held-out rows to tune a route.
        if row in relevant or record["actual_category"] != expected[row]:
            raise ValueError(f"Duplicate or mismatched reference row {row} in {path}")
        prediction = record["predicted_category"]
        if record.get("status") != "200" or prediction not in CATEGORIES:
            prediction = "ERROR"
        relevant[row] = {**record, "row": row, "predicted_category": prediction}
    if set(relevant) != set(expected):
        raise ValueError(f"Missing {len(set(expected) - set(relevant))} {split} predictions in {path}")
    return [relevant[row] for row in sorted(relevant)]


def group_accuracy(records):
    correct = sum(r["actual_category"] == r["predicted_category"] for r in records)
    return {"correct": correct, "wrong": len(records) - correct, "count": len(records),
            "accuracy_pct": 100 * correct / len(records) if records else None}


def accuracy_metrics(records):
    matrix = {actual: dict.fromkeys(CATEGORIES + ["ERROR"], 0) for actual in CATEGORIES}
    for r in records:
        matrix[r["actual_category"]][r["predicted_category"]] += 1
    result = {"overall": group_accuracy(records),
              "per_category": {cat: group_accuracy([r for r in records if r["actual_category"] == cat])
                               for cat in CATEGORIES},
              "confusion_matrix": matrix, "matrix_orientation": "rows=true, columns=prediction",
              "errors": sum(r["predicted_category"] == "ERROR" for r in records)}
    if records and "escalated" in records[0]:
        escalated = [r for r in records if r["escalated"] is True]
        accepted = [r for r in records if r["escalated"] is False]
        if len(escalated) + len(accepted) != len(records):
            raise ValueError("Missing escalation decision")
        result["cascade"] = {"escalated": len(escalated), "non_escalated": len(accepted),
                             "escalation_pct": 100 * len(escalated) / len(records),
                             "escalated_accuracy": group_accuracy(escalated),
                             "non_escalated_accuracy": group_accuracy(accepted)}
    return result


def read_logs(path):
    records = {}
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if record.get("method") != "POST" or record.get("path") != "/tickets":
                continue
            rid = record["request_id"]
            if rid in records:
                raise ValueError(f"Duplicate request ID in audit logs: {rid}")
            records[rid] = record
    return records


def attach_escalations(records, logs):
    for record in records:
        log = logs.get(record["request_id"])
        if not log or str(log.get("source_row")) != str(record["row"]):
            raise ValueError(f"Missing/mismatched service log for row {record['row']}")
        if not isinstance(log.get("escalated"), bool):
            raise ValueError("Expected a cascade log with an escalation decision")
        if record["predicted_category"] != "ERROR" and log.get("category") != record["predicted_category"]:
            raise ValueError(f"Service response differs from log at row {record['row']}")
        record["escalated"] = log["escalated"]
        record["final_model"] = log.get("final_model")
    return records


def verify_service(url, model, run_id, timeout=10):
    if "sut-ip" in url.lower():
        raise ValueError("SUT-IP is a placeholder. Omit --url for localhost or use the actual service host IP.")
    try:
        response = requests.get(url.rstrip("/") + "/stats", timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ValueError(f"Cannot connect to the triage service at {url}. Start it with "
                         f"python start_config.py --model {model} --run-id {run_id}. Details: {exc}") from exc
    for key, value in {"X-Model-Name": model, "X-Model-Digest": MODEL_DIGESTS[model],
                       "X-Run-ID": run_id, "X-Output-Format": "category-json-v1"}.items():
        if response.headers.get(key) != value:
            raise ValueError(f"Service identity mismatch: {key}={response.headers.get(key)!r}, expected {value!r}")
    return sum(response.json().values())


def classify_for_accuracy(url, model, run_id, row, narrative, actual, timeout):
    request_id = str(uuid.uuid4())
    status, predicted, error = 0, "ERROR", ""
    start = time.perf_counter()
    try:
        response = requests.post(url.rstrip("/") + "/tickets", json={"narrative": narrative},
                                 headers={"X-Request-ID": request_id, "X-Source-Row": str(row)}, timeout=timeout)
        status = response.status_code
        response.raise_for_status()
        if response.headers.get("X-Run-ID") != run_id or response.headers.get("X-Model-Digest") != MODEL_DIGESTS[model]:
            raise ValueError("Unexpected service identity")
        category = response.json()["category"]
        if category not in CATEGORIES:
            raise ValueError("Invalid category")
        predicted = category
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        error = str(exc)
    return {"row": row, "request_id": request_id, "actual_category": actual, "predicted_category": predicted,
            "status": status, "elapsed_ms": round((time.perf_counter() - start) * 1000, 3), "error": error}


def run_accuracy(args):
    if args.split == "test":
        verify_formal_inputs()
    else:
        verify_split()
    verify_service(args.url, args.model, args.run_id)
    source, expected = source_rows(), split_labels(args.split)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    save_json(out / "metadata.json", {"split": args.split, "model": args.model,
              "digest": MODEL_DIGESTS[args.model], "mode": args.mode, "run_id": args.run_id, "url": args.url})
    import csv
    with (out / "predictions.csv").open("x", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for i, (row, actual) in enumerate(sorted(expected.items()), 1):
            result = classify_for_accuracy(args.url, args.model, args.run_id, row, source[row], actual, args.timeout)
            writer.writerow(result)
            f.flush()
            print(f"{i}/{len(expected)} row={row} status={result['status']}", flush=True)


def reuse_accuracy(args):
    if args.split == "test":
        verify_formal_inputs()
    else:
        verify_split()
    records = subset_predictions(args.predictions, args.split)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    write_csv(out / "predictions.csv", [{field: r.get(field, "") for field in FIELDS} for r in records], FIELDS)
    save_json(out / "metadata.json", {"split": args.split, "model": args.model, "mode": "single",
              "digest": MODEL_DIGESTS[args.model], "reused_A1_predictions": str(Path(args.predictions).resolve()),
              "team_confirmed_unchanged": True})


def tuning_analysis(small_path, large_path, accepted_lists):
    small = subset_predictions(small_path, "tuning")
    large = {r["row"]: r for r in subset_predictions(large_path, "tuning")}
    precision = {}
    for predicted in CATEGORIES:
        group = [r for r in small if r["predicted_category"] == predicted]
        precision[predicted] = group_accuracy(group)
    trials = []
    for accepted in accepted_lists:
        routes = []
        for r in small:
            escalate = should_escalate(r["predicted_category"], accepted)
            record = dict(large[r["row"]] if escalate else r, escalated=escalate)
            routes.append(record)
        trials.append({"accepted_categories": sorted(accepted), "estimated_tuning_result": accuracy_metrics(routes)})
    return {"note": "Tuning-only offline estimates, not final measured cascade results.",
            "small_model": accuracy_metrics(small), "large_model": accuracy_metrics(list(large.values())),
            "small_model_precision_by_predicted_category": precision, "candidate_rules": trials}


def accuracy_floors(top):
    return {"overall": max(0, top["overall"]["accuracy_pct"] - 10),
            "per_category": {category: max(0, item["accuracy_pct"] - 15) if item["count"] else None
                             for category, item in top["per_category"].items()}}


def compare_reports(top_path, configurations):
    def load(path):
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        if value.get("split") != "test":
            raise ValueError(f"Not a held-out test report: {path}")
        return value
    top = load(top_path)
    floors = accuracy_floors(top)
    results = []
    for name, path in configurations:
        report = load(path)
        if report["overall"]["count"] != top["overall"]["count"]:
            raise ValueError("Test set size differs from top model")
        passes = {}
        for cat, floor in floors["per_category"].items():
            item = report["per_category"][cat]
            if item["count"] != top["per_category"][cat]["count"]:
                raise ValueError(f"Category support changed for {cat}")
            passes[cat] = floor is not None and item["accuracy_pct"] + 1e-9 >= floor
        overall_pass = report["overall"]["accuracy_pct"] + 1e-9 >= floors["overall"]
        results.append({"configuration": name, "overall_pass": overall_pass, "per_category_pass": passes,
                        "qualifies": overall_pass and all(passes.values()), "accuracy": report})
    return {"top_model": top, "floors_pct": floors, "configurations": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--split", choices=["tuning", "test"], required=True)
    run.add_argument("--model", choices=MODEL_DIGESTS, required=True)
    run.add_argument("--mode", choices=["single", "cascade"], default="single")
    run.add_argument("--url", default="http://127.0.0.1:8000", help="Triage service URL (default: local Docker service)")
    run.add_argument("--run-id", required=True)
    run.add_argument("--timeout", type=float, default=1300)
    run.add_argument("--output", required=True)
    reuse = commands.add_parser("reuse")
    reuse.add_argument("--split", choices=["tuning", "test"], required=True)
    reuse.add_argument("--model", choices=MODEL_DIGESTS, required=True)
    reuse.add_argument("--predictions", required=True)
    reuse.add_argument("--confirm-unchanged", action="store_true", required=True,
                       help="Team verified identical model digest, prompt, Ollama version and machine")
    reuse.add_argument("--output", required=True)
    tune = commands.add_parser("tune")
    tune.add_argument("--small", required=True)
    tune.add_argument("--large", required=True)
    tune.add_argument("--accept", action="append", default=[], help="Pipe-separated predicted-category acceptance list; repeat for trials")
    tune.add_argument("--output", required=True)
    score = commands.add_parser("score")
    score.add_argument("--split", choices=["tuning", "test"], required=True)
    score.add_argument("--predictions", required=True)
    score.add_argument("--cascade-logs", help="Required for cascade scoring; exact matching JSONL")
    score.add_argument("--output", required=True)
    compare = commands.add_parser("compare")
    compare.add_argument("--top", required=True)
    compare.add_argument("--config", action="append", required=True, metavar="NAME=REPORT_JSON")
    compare.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "run":
        run_accuracy(args)
    elif args.command == "reuse":
        reuse_accuracy(args)
    elif args.command == "tune":
        verify_split()
        save_json(args.output, tuning_analysis(args.small, args.large, [accept_categories(v) for v in args.accept]))
    elif args.command == "score":
        verify_split()
        records = subset_predictions(args.predictions, args.split)
        if args.cascade_logs:
            attach_escalations(records, read_logs(args.cascade_logs))
        report = accuracy_metrics(records)
        save_json(args.output, {"split": args.split, **report})
        print(json.dumps(report, indent=2))
    else:
        verify_split()
        save_json(args.output, compare_reports(args.top, [value.split("=", 1) for value in args.config]))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, requests.RequestException) as exc:
        raise SystemExit(str(exc))
