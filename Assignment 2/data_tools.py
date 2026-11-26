"""Prepare and verify fixed Assignment 2 inputs without changing Assignment 1."""
import base64
import csv
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess

from categories import CATEGORIES

ROOT = Path(__file__).resolve().parent
A1 = ROOT.parent / "Assignment 1"
DATA = ROOT / "data"
GOLDEN = A1 / "data/team11/golden.csv"
SOURCE = A1 / "data/team11/team_tickets.csv"


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with Path(path).open("x", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def source_rows():
    rows = read_csv(SOURCE)
    result = {int(r["row"]): r["narrative"] for r in rows}
    if len(rows) != 1000 or set(result) != set(range(11000, 12000)) or not all(s.strip() for s in result.values()):
        raise ValueError("Assignment 1 Team 11 source data is invalid")
    return result


def labels(path):
    rows = read_csv(path)
    result = {int(r["row"]): r["category"] for r in rows}
    if len(rows) != len(result) or not set(result) <= set(range(11000, 12000)) or not set(result.values()) <= set(CATEGORIES):
        raise ValueError(f"Invalid labels: {path}")
    return result


def verify_split():
    original = labels(GOLDEN)
    if len(original) != 175:
        raise ValueError("Expected 175 frozen golden labels")
    for name, parity in (("tuning", 1), ("test", 0)):
        expected = {row: cat for row, cat in original.items() if row % 2 == parity}
        path = DATA / f"golden_{name}.csv"
        if labels(path) != expected:
            raise ValueError(f"Split does not match original source-row parity: {path}")
        raw_rows = [int(r["row"]) for r in read_csv(path)]
        if raw_rows != sorted(raw_rows):
            raise ValueError(f"Split is not sorted: {path}")
    return original


def git_executable():
    """Resolve Git in normal terminals and permit an explicit portable installation."""
    override = os.getenv("GIT_EXE")
    if override:
        executable = shutil.which(override)
        if executable:
            return executable
        raise ValueError(f"GIT_EXE does not point to an executable Git installation: {override}")
    executable = shutil.which("git")
    if executable:
        return executable
    if os.name == "nt":
        installs = [Path(os.environ[name]) / "Git/cmd/git.exe"
                    for name in ("ProgramFiles", "ProgramFiles(x86)") if os.environ.get(name)]
        if os.environ.get("LOCALAPPDATA"):
            installs.append(Path(os.environ["LOCALAPPDATA"]) / "Programs/Git/cmd/git.exe")
        for path in installs:
            if path.is_file():
                return str(path)
    raise ValueError("Git is required for formal assignment commit checks but is not on PATH. "
                     "Install Git or set GIT_EXE to the full path of git.exe, then retry.")


def require_committed(*paths):
    git = git_executable()
    root = Path(subprocess.check_output([git, "rev-parse", "--show-toplevel"], cwd=ROOT, text=True).strip()).resolve()
    for path in paths:
        path = Path(path).resolve()
        rel = path.relative_to(root).as_posix()
        try:
            old = subprocess.check_output([git, "show", f"HEAD:{rel}"], cwd=ROOT, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as exc:
            raise ValueError(f"Commit {rel} before collecting assignment measurements") from exc
        if old.replace(b"\r\n", b"\n") != path.read_bytes().replace(b"\r\n", b"\n"):
            raise ValueError(f"Commit the current version of {rel} before measuring")


def require_split_commit():
    verify_split()
    require_committed(GOLDEN, DATA / "golden_tuning.csv", DATA / "golden_test.csv")


def require_test_commit():
    require_split_commit()
    paths = [ROOT / "predictions.md", ROOT / "escalation_rule.md"]
    for path in paths:
        if "[TEAM TO COMPLETE]" in path.read_text(encoding="utf-8"):
            raise ValueError(f"Complete {path.name} before formal tests")
    require_committed(*paths)


def verify_formal_inputs():
    """Validate the dataset; Git history is submission evidence, not a runtime dependency."""
    verify_split()
    for name in ("predictions.md", "escalation_rule.md"):
        path = ROOT / name
        if not path.is_file() or "[TEAM TO COMPLETE]" in path.read_text(encoding="utf-8"):
            print(f"Reminder: complete and commit {name} before collecting formal Assignment 2 results.", flush=True)


def fixed_rows(name):
    path = DATA / f"{name}_rows.txt"
    rows = [int(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(set(rows)) != len(rows) or not set(rows) <= set(source_rows()) - set(verify_split()):
        raise ValueError(f"Invalid non-golden row list: {path}")
    return rows


def prepare_workload():
    original, source = verify_split(), source_rows()
    eligible = sorted(set(source) - set(original))
    rng = random.Random(31130211)
    typical = [row for row in eligible if 700 <= len(source[row]) <= 950]
    rng.shuffle(typical)
    warmup, calibration = typical[:3], typical[3:6]
    remaining = [row for row in eligible if row not in warmup + calibration]
    long = [row for row in remaining if len(source[row]) >= 1658]
    others = [row for row in remaining if row not in set(long)]
    rng.shuffle(long)
    rng.shuffle(others)
    # Put a long ticket in each block of five while long tickets remain. Every run
    # consumes a fixed prefix, with no recycling or warm-up/calibration overlap.
    ordered = []
    while long or others:
        for _ in range(4):
            if others:
                ordered.append(others.pop())
        if long:
            ordered.append(long.pop())
    for name, rows in (("warmup", warmup), ("calibration", calibration), ("workload", ordered)):
        path = DATA / f"{name}_rows.txt"
        with path.open("x", encoding="utf-8") as f:
            f.write("".join(f"{row}\n" for row in rows))
    write_csv(DATA / "speed_workload.csv", ({"row": row, "payload_b64": base64.b64encode(
        json.dumps({"narrative": source[row]}, ensure_ascii=False).encode()).decode()} for row in ordered),
        ["row", "payload_b64"])
    print(f"Prepared {len(warmup)} warm-up, {len(calibration)} calibration, and {len(ordered)} ordered speed tickets")


if __name__ == "__main__":
    prepare_workload()
