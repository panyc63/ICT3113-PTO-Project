"""Run the Step 4-1 Qwen benchmark on the frozen even-row test tickets."""
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
    run_id = new_run_id("qwen")
    run_single_model(TOP_MODEL, run_id, STEP_DIR / "results" / run_id, STEP_DIR / "logs" / run_id)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError, requests.RequestException) as exc:
        sys.exit(str(exc))
