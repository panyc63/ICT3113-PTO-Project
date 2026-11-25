"""Prepare team-only traffic and blank label sheets without calling the model."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import random
import statistics
from dataset import DEFAULT_DATASET, DEFAULT_TEAM, team_rows, write_csv


def prepare(dataset, team, output, sample_size=175, seed=3113):
    if not 150 <= sample_size <= 200:
        raise ValueError("Golden sample size must be 150 to 200")
    source = team_rows(dataset, team)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)  # Never overwrite human labels.
    rows = list(source.values())
    write_csv(output / "team_tickets.csv", ["row", "narrative"],
              ({"row": r["row"], "narrative": r["narrative"]} for r in rows))
    # Preserve multiline narratives as one line per ticket for JMeter CSV input.
    write_csv(output / "jmeter_tickets.csv", ["row", "payload_b64"], ({
        "row": r["row"],
        "payload_b64": base64.b64encode(json.dumps({"narrative": r["narrative"]},
                                                 ensure_ascii=False).encode("utf-8")).decode("ascii"),
    } for r in rows))
    sample = sorted(random.Random(seed).sample(rows, sample_size), key=lambda r: r["row"])
    blanks = [{"row": r["row"], "narrative": r["narrative"], "category": ""} for r in sample]
    for name in ("labels_member1.csv", "labels_member2.csv"):
        write_csv(output / name, ["row", "narrative", "category"], blanks)
    lengths = sorted(len(r["narrative"]) for r in rows)
    summary = {
        "team": team, "first_row": min(source), "last_row": max(source), "count": len(rows),
        "source_file": str(Path(dataset).resolve()),
        "source_sha256": hashlib.sha256(Path(dataset).read_bytes()).hexdigest(),
        "sample_size": sample_size, "sample_seed": seed,
        "golden_sample_rows": [r["row"] for r in sample],
        "narrative_characters": {"min": lengths[0], "median": statistics.median(lengths),
                                 "p95_nearest_rank": lengths[949], "max": lengths[-1]},
    }
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--team", type=int, default=DEFAULT_TEAM)
    parser.add_argument("--output", type=Path, default=Path("data/team11"))
    parser.add_argument("--sample-size", type=int, default=175)
    parser.add_argument("--seed", type=int, default=3113)
    args = parser.parse_args()
    result = prepare(args.dataset, args.team, args.output, args.sample_size, args.seed)
    print(f"Prepared {result['count']} tickets and {result['sample_size']} blank labels in {args.output}")
