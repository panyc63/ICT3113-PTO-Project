"""Memory evidence, calibration, JMeter execution and summary for Assignment 2."""
import argparse
import csv
import json
import math
from pathlib import Path
import statistics
import subprocess
import time
import uuid

import requests

from accuracy import read_logs, save_json, verify_service
from data_tools import DATA, ROOT, fixed_rows, read_csv, verify_formal_inputs, source_rows
from model_config import MODEL_DIGESTS, generate_payload, parse_category, verify_installed_models


def timing_parameters(s):
    if not math.isfinite(s) or s <= 0:
        raise ValueError("S must be positive")
    timeout = max(300, math.ceil(10 * s))
    return {"S_seconds": s, "rate_per_hour": 1800 / s, "duration_seconds": math.ceil(max(5, s) * 60),
            "timeout_seconds": timeout, "drain_seconds": timeout + 60,
            "client_peak_tickets_per_hour": 157.332692, "covers_client_peak": 1800 / s >= 157.332692}


def warmup(args):
    # Run on SUT after restarting Ollama; direct identical prompts load both models.
    # This is a model-residency preflight, not an accuracy or speed measurement.
    # fixed_rows validates the frozen split and eligibility without needing Git.
    source, rows = source_rows(), fixed_rows("warmup")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise ValueError(f"Warm-up evidence already exists: {output}; select a new output file")
    host = args.ollama.rstrip("/")
    if len(set(args.model)) != len(args.model):
        raise ValueError("Duplicate model")
    tags = requests.get(host + "/api/tags", timeout=10)
    tags.raise_for_status()
    installed = {m["name"]: m["digest"] for m in tags.json()["models"]}
    verify_installed_models(installed, args.model)
    calls = []
    # Interleave to demonstrate residency instead of just loading one at a time.
    for row in rows:
        for model in args.model:
            print(f"Warming {model} with row {row}...", flush=True)
            res = requests.post(host + "/api/generate", json=generate_payload(model, source[row]), timeout=args.timeout)
            res.raise_for_status()
            try:
                category = parse_category(res.json()["response"])
            except (KeyError, ValueError, TypeError):
                category = "ERROR"
            calls.append({"row": row, "model": model, "category": category})
    ps = requests.get(host + "/api/ps", timeout=10)
    ps.raise_for_status()
    resident = {m["name"]: m for m in ps.json()["models"]}
    cpu_only = all(resident.get(model, {}).get("size_vram") == 0 for model in args.model)
    both_resident = set(args.model) <= set(resident)
    cli = subprocess.run(["docker", "compose", "exec", "-T", "ollama", "ollama", "ps"], cwd=ROOT,
                         capture_output=True, text=True, check=False)
    evidence = {"models": args.model, "warmup_calls": calls, "ollama_ps": cli.stdout, "ollama_ps_stderr": cli.stderr,
                "resident_models": list(resident.values()), "all_resident": both_resident, "cpu_only": cpu_only}
    save_json(args.output, evidence)
    print(cli.stdout)
    if not (both_resident and cpu_only and cli.returncode == 0):
        raise ValueError("Residency/CPU check failed; retain the evidence and try a smaller pair")


def calibrate(args):
    verify_formal_inputs()
    verify_service(args.url, args.model, args.run_id)
    source, rows = source_rows(), fixed_rows("calibration")
    timings = []
    for row in rows:
        started = time.perf_counter()
        res = requests.post(args.url.rstrip("/") + "/tickets", json={"narrative": source[row]},
                            headers={"X-Request-ID": str(uuid.uuid4()), "X-Source-Row": str(row)}, timeout=args.timeout)
        elapsed = time.perf_counter() - started
        res.raise_for_status()
        if res.headers.get("X-Run-ID") != args.run_id:
            raise ValueError("Unexpected service identity")
        timings.append({"row": row, "seconds": elapsed})
    params = timing_parameters(statistics.median(t["seconds"] for t in timings))
    save_json(args.output, {"model": args.model, "run_id": args.run_id, "timings": timings, **params})
    print(json.dumps(params, indent=2))


def run_jmeter(args):
    verify_formal_inputs()
    warm = json.loads(Path(args.warmup_evidence).read_text(encoding="utf-8"))
    if not warm.get("all_resident") or not warm.get("cpu_only") or args.model not in warm["models"]:
        raise ValueError("Run warm-up/residency check before starting JMeter")
    params = json.loads(Path(args.calibration).read_text(encoding="utf-8"))
    if params["duration_seconds"] * params["rate_per_hour"] / 3600 > len(fixed_rows("workload")) - 30:
        raise ValueError("Arrival schedule risks exhausting the fixed unique workload")
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    before = verify_service(args.url, args.model, args.run_id)
    from urllib.parse import urlsplit
    url = urlsplit(args.url)
    if url.scheme != "http" or (url.path not in ("", "/")):
        raise ValueError("Use http://SUT-IP:8000 for the test service")
    properties = {"host": url.hostname, "port": url.port or 80, "rate_hour": params["rate_per_hour"],
                  "duration_sec": params["duration_seconds"], "drain_sec": params["drain_seconds"],
                  "timeout_ms": params["timeout_seconds"] * 1000,
                  "workload_csv": (DATA / "speed_workload.csv").as_posix(), "starts_csv": (out / "starts.csv").as_posix(),
                  "sample_variables": "row,request_id", "jmeter.save.saveservice.output_format": "csv",
                  "jmeter.save.saveservice.print_field_names": "true", "jmeter.save.saveservice.timestamp_format": "ms",
                  "jmeter.save.saveservice.time": "true", "jmeter.save.saveservice.successful": "true",
                  "jmeter.save.saveservice.label": "true", "jmeter.save.saveservice.response_code": "true"}
    cmd = [args.jmeter, "-n", "-t", str(ROOT / "jmeter/assignment2-load-test.jmx"), "-l", str(out / "run.jtl"),
           "-j", str(out / "jmeter.log"), *[f"-J{k}={v}" for k, v in properties.items()]]
    (out / "starts.csv").write_text("row,request_id,start_ms\n", encoding="utf-8")
    save_json(out / "setup.json", {"run_id": args.run_id, "model": args.model, "stats_before": before,
                                  "calibration": params, "warmup_evidence": warm, "command": cmd})
    result = subprocess.run(cmd, check=False)
    after = verify_service(args.url, args.model, args.run_id)
    save_json(out / "stats.json", {"before": before, "after": after, "jmeter_exit_code": result.returncode})
    if result.returncode != 0:
        print("JMeter returned a nonzero exit code; retain this run and investigate.")


def percentile(values, q):
    if not values:
        return None
    values = sorted(values)
    return values[max(0, math.ceil(q * len(values)) - 1)]


def summarize_run(folder, log_path):
    folder = Path(folder)
    starts_list = read_csv(folder / "starts.csv")
    starts = {r["request_id"]: r for r in starts_list}
    if len(starts) != len(starts_list):
        raise ValueError("Duplicate start IDs")
    rows = [r for r in read_csv(folder / "run.jtl") if r["label"] == "POST /tickets"]
    result_ids = {r["request_id"] for r in rows}
    if len(result_ids) != len(rows) or not result_ids <= set(starts):
        raise ValueError("JTL has duplicate or unknown requests")
    ordered = [int(r["row"]) for r in starts_list]
    if len(ordered) != len(set(ordered)) or set(ordered) != set(fixed_rows("workload")[:len(ordered)]):
        raise ValueError("Load run did not use the expected unique workload prefix")
    stats = json.loads((folder / "stats.json").read_text(encoding="utf-8"))
    setup = json.loads((folder / "setup.json").read_text(encoding="utf-8"))
    logs = read_logs(log_path)
    logs = {rid: r for rid, r in logs.items() if rid in starts}
    success = [r for r in rows if r["success"].lower() == "true"]
    errors = len(rows) - len(success)
    latencies = [int(r["elapsed"]) for r in success]
    finished = stats["after"] - stats["before"]
    stored = sum(r.get("ticket_id") is not None and r.get("status") == 200 for r in logs.values())
    # Throughput is completions per offered-load duration; separately report drain and count mismatch.
    seconds = setup["calibration"]["duration_seconds"]
    decisions = [r["escalated"] for r in logs.values() if isinstance(r.get("escalated"), bool)]
    return {"run": setup["run_id"], "sent": len(starts), "completed_stored": finished,
            "successful_jtl": len(success), "errored_jtl": errors, "unfinished_jtl": len(starts) - len(rows),
            "logs_found": len(logs), "stored_logs": stored, "stats_match_logs": stored == finished,
            "p50_ms": statistics.median(latencies) if latencies else None,
            "throughput_completed_per_second": finished / seconds,
            "throughput_denominator_seconds": seconds,
            "error_rate_pct": 100 * errors / len(starts) if starts else None,
            "escalated": sum(decisions) if decisions else None, "escalation_denominator": len(decisions),
            "escalation_pct": 100 * sum(decisions) / len(decisions) if decisions else None,
            "jmeter_exit_code": stats["jmeter_exit_code"], "successful_elapsed_ms": latencies}


def summarize(runs):
    if len(runs) != 3:
        raise ValueError("Exactly three runs are required")
    medians = [r["p50_ms"] for r in runs]
    pooled = [v for r in runs for v in r["successful_elapsed_ms"]]
    return {"runs": runs, "mean_p50_ms": statistics.mean(medians) if all(v is not None for v in medians) else None,
            "p50_spread_ms": max(medians) - min(medians) if all(v is not None for v in medians) else None,
            "p50_stddev_ms": statistics.stdev(medians) if all(v is not None for v in medians) else None,
            "pooled_p95_ms": percentile(pooled, 0.95), "pooled_sample_count": len(pooled)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    subs = p.add_subparsers(dest="command", required=True)
    warm = subs.add_parser("warmup")
    warm.add_argument("--model", choices=MODEL_DIGESTS, action="append", required=True)
    warm.add_argument("--ollama", default="http://localhost:11434")
    warm.add_argument("--timeout", type=float, default=600)
    warm.add_argument("--output", required=True)
    cal = subs.add_parser("calibrate")
    run = subs.add_parser("run")
    for sub in (cal, run):
        sub.add_argument("--model", choices=MODEL_DIGESTS, required=True)
        sub.add_argument("--url", required=True)
        sub.add_argument("--run-id", required=True)
        sub.add_argument("--output", required=True)
    cal.add_argument("--timeout", type=float, default=1300)
    run.add_argument("--jmeter", default="jmeter")
    run.add_argument("--calibration", required=True)
    run.add_argument("--warmup-evidence", required=True)
    summary = subs.add_parser("summary")
    summary.add_argument("--run", nargs=2, action="append", required=True, metavar=("RUN_DIR", "SERVICE_LOG"))
    summary.add_argument("--output", required=True)
    args = p.parse_args()
    if args.command == "warmup":
        warmup(args)
    elif args.command == "calibrate":
        calibrate(args)
    elif args.command == "run":
        run_jmeter(args)
    else:
        save_json(args.output, summarize([summarize_run(*run) for run in args.run]))


if __name__ == "__main__":
    main()
