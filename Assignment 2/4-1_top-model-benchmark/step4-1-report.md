# Step 4-1 — Test the top model alone

**Qwen2.5 7B passes overall and in all seven categories.** In the fresh A2 run on 27 November 2026, Qwen alone scored **62 right and 28 wrong (68.89%)**. Step 1 sets the limits from the archived A1 predictions on these same rows (63 right, 27 wrong). The fresh run clears the 54-ticket overall minimum by eight tickets. [Step 1 limits](../1_accuracy-limits/step1-report.md) · [A2 score and confusion matrix](results/qwen-20261127T113825Z-3a6842ff/accuracy.json)

## Which tickets count?

The team sorted the 175 A1 golden tickets by their original source row number and committed both lists on 25 November. The **85 odd-numbered rows** are reserved for designing and adjusting the escalation rule. The **90 even-numbered rows** are the test set for comparing every configuration. All 175 tickets had already been evaluated in A1, so this split supports a fair comparison on the same tickets. Performance on previously unseen complaints remains unmeasured. [Split commit](https://github.com/panyc63/ICT3113-PTO-Project/commit/998344b1d946a28b9fed7f5f796cf421fdd96dcf) · [Tuning rows](../data/golden_tuning.csv) · [Test rows](../data/golden_test.csv)

## How did Qwen compare with the Step 1 limits?

The right and wrong counts below are from the fresh A2 run. The floor and minimum columns come from Step 1. Percentages are rounded to two decimals.

| True category | Test tickets | Qwen right | Qwen wrong | Qwen accuracy | A2 accuracy floor | Minimum right to pass |
|---|---:|---:|---:|---:|---:|---:|
| **Overall** | **90** | **62** | **28** | **68.89%** | **60.00%** | **54** |
| Credit reporting | 20 | 14 | 6 | 70.00% | 55.00% | 11 |
| Debt collection | 13 | 10 | 3 | 76.92% | 61.92% | 9 |
| Mortgage | 11 | 7 | 4 | 63.64% | 48.64% | 6 |
| Credit card | 7 | 4 | 3 | 57.14% | 42.14% | 3 |
| Bank account or service | 18 | 13 | 5 | 72.22% | 57.22% | 11 |
| Consumer loan | 10 | 8 | 2 | 80.00% | 65.00% | 7 |
| Money transfer or service | 11 | 6 | 5 | 54.55% | 48.64% | 6 |

**Credit card is the least stable category.** With only seven tickets, one changed answer moves accuracy by 14.29 percentage points, almost the entire 15-point allowance. Three right and four wrong passes the category floor. Two right and five wrong fails it. The threshold still applies, but seven tickets give weak evidence about performance on credit card complaints generally.

## What did the run measure?

Each even-row ticket went through `POST /tickets` once for classification. All 90 requests succeeded. The evaluator compared each prediction with the frozen label and separately asked Qwen for a confidence score. All 90 scores were recorded. Accuracy depends only on whether the predicted category matched the label. The request ID connects the prediction to the ticket narrative and the service log. [Predictions](results/qwen-20261127T113825Z-3a6842ff/predictions.csv) · [Ticket log](logs/qwen-20261127T113825Z-3a6842ff/qwen-20261127T113825Z-3a6842ff.tickets.jsonl) · [Service log](logs/qwen-20261127T113825Z-3a6842ff/qwen-20261127T113825Z-3a6842ff.jsonl)

The `accuracy_floors_pct` field in the original A2 run output describes the floors that this run alone would imply. The figures used for Step 4 comparisons are in the [Step 1 reference](../1_accuracy-limits/a2-test-rows/accuracy.json). Qwen’s speed baseline requires the worksheet’s separate calibrated, three-run JMeter test.
