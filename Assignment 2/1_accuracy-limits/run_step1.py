"""Benchmark every A1 model on tuning, then set the limits using Qwen on test."""
import argparse
from pathlib import Path
import subprocess
import sys

import requests

STEP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(STEP_DIR.parent))

from data_tools import verify_formal_inputs
from single_model_benchmark import TOP_MODEL, new_run_id, run_single_model


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    verify_formal_inputs()
    batch = new_run_id("step1")
    for split, model, folder in (
        ("tuning", "llama3.2:1b", "llama-1b"),
        ("tuning", "llama3.2:3b", "llama-3b"),
        ("tuning", TOP_MODEL, "qwen-7b"),
        ("test", TOP_MODEL, "qwen-7b"),
    ):
        relative = Path(batch) / split / folder
        print(f"Starting {model} on {split} tickets", flush=True)
        run_single_model(model, f"{batch}-{split}-{folder}",
                         STEP_DIR / "results" / relative, STEP_DIR / "logs" / relative,
                         split=split)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError, requests.RequestException) as exc:
        sys.exit(str(exc))
