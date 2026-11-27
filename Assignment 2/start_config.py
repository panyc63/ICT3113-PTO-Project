"""Start a single-model or cascade configuration without PowerShell execution policy or Git."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import requests

from model_config import MODEL_DIGESTS, accept_categories

ROOT = Path(__file__).resolve().parent


def compose(env, *args):
    result = subprocess.run(["docker", "compose", *args], cwd=ROOT, env=env)
    if result.returncode:
        raise RuntimeError(f"Docker Compose failed (exit {result.returncode}). See the output above.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=MODEL_DIGESTS)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--large-model", choices=MODEL_DIGESTS)
    parser.add_argument("--setting", choices=["1", "2"])
    parser.add_argument("--accept-categories", default="")
    parser.add_argument("--model-timeout", type=int, default=600)
    parser.add_argument("--log-dir", type=Path, default=ROOT / "logs", help="Host directory for the service audit log")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.run_id):
        parser.error("Run ID must contain only letters, numbers, dots, underscores or hyphens")
    if args.large_model and (args.large_model == args.model or not args.setting):
        parser.error("Cascade requires a distinct large model and --setting 1 or 2")
    accept_categories(args.accept_categories)
    if args.model_timeout <= 0:
        parser.error("Model timeout must be positive")
    state_file = ROOT / ".ollama-reuse.json"
    if not state_file.exists() or not (ROOT / ".env").exists():
        subprocess.run([sys.executable, str(ROOT / "0_setup" / "setup_ollama.py")], cwd=ROOT, check=True)
    state = json.loads(state_file.read_text(encoding="utf-8"))
    env = os.environ.copy()
    env.update({"A2_OLLAMA_IMAGE": state["image"], "A2_OLLAMA_VOLUME_NAME": state["volume"],
                "MODE": "cascade" if args.large_model else "single", "MODEL_NAME": args.model,
                "MODEL_DIGEST": MODEL_DIGESTS[args.model], "LARGE_MODEL": args.large_model or "",
                "LARGE_MODEL_DIGEST": MODEL_DIGESTS.get(args.large_model, ""),
                "CASCADE_SETTING": args.setting or "", "ACCEPT_CATEGORIES": args.accept_categories,
                "RUN_ID": args.run_id, "MODEL_TIMEOUT": str(args.model_timeout)})
    log_dir = args.log_dir.resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    env["TRIAGE_LOG_DIR"] = log_dir.as_posix()
    if (log_dir / f"{args.run_id}.jsonl").exists():
        print("Existing log will be preserved and appended to. Use a distinct run ID for each separate measured run.", flush=True)
    compose(env, "up", "-d", "--wait", "ollama")
    compose(env, "up", "-d", "--build", "--force-recreate", "--no-deps", "triage-service")
    print("Waiting for the triage service on http://127.0.0.1:8000 ...", flush=True)
    expected = {"X-Model-Name": args.model, "X-Model-Digest": MODEL_DIGESTS[args.model], "X-Run-ID": args.run_id}
    deadline = time.monotonic() + 60
    last_error = "Service not ready"
    while time.monotonic() < deadline:
        try:
            response = requests.get("http://127.0.0.1:8000/stats", timeout=3)
            response.raise_for_status()
            if all(response.headers.get(key) == value for key, value in expected.items()):
                print(f"Ready: {args.model}, run ID {args.run_id}. Use localhost:8000 for local tuning.")
                return
            last_error = "Service responded with a different model/run ID."
        except requests.RequestException as exc:
            last_error = str(exc)
        time.sleep(1)
    compose(env, "logs", "--tail", "60", "triage-service")
    raise RuntimeError(f"Triage service did not become ready: {last_error}")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        sys.exit(str(exc))
