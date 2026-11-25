"""Client-side dataset validation. Never imported by the service."""
import csv
from pathlib import Path
from categories import CATEGORIES

DEFAULT_DATASET = Path(__file__).resolve().parent / "data" / "ict3113_tickets.csv"
DEFAULT_TEAM = 11


def read_csv(path, required):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not set(required).issubset(reader.fieldnames or []):
            raise ValueError(f"{path}: required columns are {', '.join(required)}")
        return list(reader)


def team_rows(path=DEFAULT_DATASET, team=DEFAULT_TEAM):
    if team < 0:
        raise ValueError("Team number must be non-negative")
    start = team * 1000
    selected = {}
    for item in read_csv(path, ("row", "source_label", "narrative")):
        row = int(item["row"])
        if start <= row < start + 1000:
            if row in selected:
                raise ValueError(f"Duplicate source row {row}")
            if not item["narrative"].strip() or item["source_label"] not in CATEGORIES:
                raise ValueError(f"Invalid source row {row}")
            selected[row] = {**item, "row": row}
    if len(selected) != 1000:
        raise ValueError(f"Team {team} needs exactly rows {start} through {start + 999}; found {len(selected)}")
    return selected


def label_rows(path, allowed):
    labels = {}
    for item in read_csv(path, ("row", "category")):
        row = int(item["row"])
        if row not in allowed or row in labels:
            raise ValueError(f"Out-of-team or duplicate row {row} in {path}")
        if item["category"] not in CATEGORIES:
            raise ValueError(f"Missing or invalid category for row {row} in {path}")
        labels[row] = item["category"]
    if not 150 <= len(labels) <= 200:
        raise ValueError("Each completed label sheet/golden set must contain 150 to 200 tickets")
    return labels


def write_csv(path, fields, rows):
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
