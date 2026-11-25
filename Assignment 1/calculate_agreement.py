"""Compare independent human labels using source row IDs, not row positions."""
import argparse
from collections import Counter
import json
from pathlib import Path
from dataset import DEFAULT_DATASET, DEFAULT_TEAM, label_rows, team_rows, write_csv


def evaluate_agreement(annotator1_csv, annotator2_csv, dataset=DEFAULT_DATASET,
                       team=DEFAULT_TEAM, output="results/agreement"):
    allowed = team_rows(dataset, team)
    first = label_rows(annotator1_csv, allowed)
    second = label_rows(annotator2_csv, allowed)
    if first.keys() != second.keys():
        raise ValueError("Annotators must label exactly the same rows; no silent inner join")
    size = len(first)
    observed = sum(first[row] == second[row] for row in first) / size
    a, b = Counter(first.values()), Counter(second.values())
    expected = sum(a[cat] * b[cat] for cat in a) / size ** 2
    kappa = (observed - expected) / (1 - expected) if expected < 1 else None
    disagreements = [{"row": row, "category_a1": first[row], "category_a2": second[row],
                      "resolved_category": "", "resolution_reason": "", "protocol_revision": ""}
                     for row in sorted(first) if first[row] != second[row]]
    report = {"ticket_count": size, "raw_agreement": observed, "cohen_kappa": kappa,
              "disagreements": len(disagreements)}
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / "disagreements_for_review.csv",
              ["row", "category_a1", "category_a2", "resolved_category", "resolution_reason", "protocol_revision"],
              disagreements)
    (output / "agreement.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("annotator1_csv")
    parser.add_argument("annotator2_csv")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--team", type=int, default=DEFAULT_TEAM)
    parser.add_argument("--output", default="results/agreement")
    args = parser.parse_args()
    print(json.dumps(evaluate_agreement(**vars(args)), indent=2))
