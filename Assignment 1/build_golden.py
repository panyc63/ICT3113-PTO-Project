"""Merge independent labels and recorded human resolutions into a golden CSV."""
import argparse
from collections import Counter
import csv
from pathlib import Path

from categories import CATEGORIES
from dataset import DEFAULT_DATASET, DEFAULT_TEAM, label_rows, read_csv, team_rows


def build_golden(annotator1_csv, annotator2_csv, resolutions, output,
                 dataset=DEFAULT_DATASET, team=DEFAULT_TEAM):
    allowed = team_rows(dataset, team)
    first = label_rows(annotator1_csv, allowed)
    second = label_rows(annotator2_csv, allowed)
    if first.keys() != second.keys():
        raise ValueError("Both annotators must label exactly the same rows")
    disputed = {row for row in first if first[row] != second[row]}
    decisions = {}
    if resolutions is not None:
        fields = ("row", "category_a1", "category_a2", "resolved_category", "resolution_reason")
        for item in read_csv(resolutions, fields):
            row = int(item["row"])
            if row not in disputed or row in decisions:
                raise ValueError(f"Unexpected or duplicate resolution row {row}; regenerate agreement after changing labels")
            if (item["category_a1"], item["category_a2"]) != (first[row], second[row]):
                raise ValueError(f"Stale resolution for row {row}: original labels have changed")
            category = item["resolved_category"]
            if category not in CATEGORIES or not (item["resolution_reason"] or "").strip():
                raise ValueError(f"Row {row} needs a valid resolved_category and a written resolution_reason")
            decisions[row] = category
    missing = sorted(disputed - decisions.keys())
    if missing:
        raise ValueError(f"{len(missing)} unresolved disagreements; first row: {missing[0]}. Complete the resolution sheet first")
    final = {row: decisions.get(row, first[row]) for row in sorted(first)}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects an existing or frozen golden set.
    with output.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["row", "category"])
        writer.writeheader()
        writer.writerows({"row": row, "category": category} for row, category in final.items())
    return {"tickets": len(final), "agreements": len(final) - len(disputed),
            "human_resolutions": len(disputed), "category_counts": dict(Counter(final.values()))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotator1-csv", default="data/team11/labels_member1.csv")
    parser.add_argument("--annotator2-csv", default="data/team11/labels_member2.csv")
    parser.add_argument("--resolutions", help="Completed disagreements_for_review.csv; omit if all labels agree")
    parser.add_argument("--output", default="data/team11/golden.csv")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--team", type=int, default=DEFAULT_TEAM)
    args = parser.parse_args()
    try:
        report = build_golden(**vars(args))
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Cannot build golden set: {exc}\n")
    print(f"Created {args.output}: {report['agreements']} agreements, "
          f"{report['human_resolutions']} recorded human resolutions.")
    absent = [cat for cat in CATEGORIES if cat not in report["category_counts"]]
    if absent:
        print("Categories with no examples: " + ", ".join(absent))
    print("Merging does not verify that labels were independently reviewed. Placeholder labels are for workflow checks only.")
