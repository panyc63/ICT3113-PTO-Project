"""Test the other A1 candidates individually against the Qwen accuracy limits."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import requests

STEP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(STEP_DIR.parent))

from accuracy import accuracy_metrics, compare_reports, save_json, subset_predictions
from data_tools import ROOT, verify_formal_inputs
from model_config import MODEL_DIGESTS
from single_model_benchmark import TOP_MODEL, new_run_id, run_single_model

CANDIDATES = {"llama3.2:1b": "llama-1b", "llama3.2:3b": "llama-3b"}


def qwen_baseline(path):
    if path is None:
        path = ROOT / "1_accuracy-limits" / "a2-test-rows" / "accuracy.json"
    path = path.resolve()
    report = json.loads(path.read_text(encoding="utf-8"))
    # Older accuracy runs store the model identity in a separate metadata file.
    identity = report if "model" in report else json.loads(
        path.with_name("metadata.json").read_text(encoding="utf-8"))
    if (report.get("split") != "test" or identity.get("model") != TOP_MODEL
            or identity.get("digest") != MODEL_DIGESTS[TOP_MODEL] or identity.get("mode", "single") != "single"):
        raise ValueError(f"Expected a held-out, single-model Qwen baseline with the A1 digest: {path}")
    predictions = subset_predictions(path.with_name("predictions.csv"), "test")
    metrics = accuracy_metrics(predictions)
    if any(report.get(key) != value for key, value in metrics.items()):
        raise ValueError(f"Qwen report disagrees with its frozen test-row predictions: {path}")
    return path, identity["run_id"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=CANDIDATES, help="Run one candidate; the default runs both in order.")
    parser.add_argument("--baseline", type=Path, help="Override the Step 1 A1-derived Qwen test report.")
    args = parser.parse_args()
    verify_formal_inputs()
    baseline, qwen_run_id = qwen_baseline(args.baseline)
    print(f"Qwen baseline: {baseline} (run {qwen_run_id})", flush=True)

    batch = new_run_id("step4-2")
    results = STEP_DIR / "results" / batch
    results.mkdir(parents=True, exist_ok=False)
    reports = []
    for model in ([args.model] if args.model else CANDIDATES):
        name = CANDIDATES[model]
        report = run_single_model(model, f"{batch}-{name}", results / name, STEP_DIR / "logs" / batch / name)
        reports.append((model, report))

    comparison = compare_reports(baseline, reports)
    comparison["baseline_run_id"] = qwen_run_id
    comparison["baseline_report"] = (baseline.relative_to(ROOT) if baseline.is_relative_to(ROOT) else baseline).as_posix()
    save_json(results / "comparison.json", comparison)
    for item in comparison["configurations"]:
        failed = [category for category, passed in item["per_category_pass"].items() if not passed]
        overall = item["accuracy"]["overall"]
        eligibility = "qualifies for speed testing" if item["qualifies"] else "fails the accuracy limits"
        print(f"{item['configuration']}: {overall['correct']}/{overall['count']} correct "
              f"({overall['accuracy_pct']:.2f}%), {eligibility}. "
              f"Overall floor: {comparison['floors_pct']['overall']:.2f}%. Failed categories: {', '.join(failed) or 'none'}.")
    print(f"Comparison: {results / 'comparison.json'}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError, requests.RequestException) as exc:
        sys.exit(str(exc))
