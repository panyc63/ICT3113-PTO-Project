# Step 1 — Compare tuning models and define the accuracy limits

**The new overall floor is 55/90 (61.11%).** Qwen2.5 7B scored 64 right and 26 wrong (71.11%) on the even-row test set. A configuration must also meet each of the seven category floors below.

## How did all three models perform on tuning?

Each A1 model classified the same 85 odd source rows independently. The table groups tickets by their true category. Each cell shows **right / wrong (accuracy)**. These tuning results help design the escalation rule. Qualification uses the held-out test rows. [Frozen tuning rows](../data/golden_tuning.csv)

| True category | Tickets | Llama 3.2 1B | Llama 3.2 3B | Qwen2.5 7B |
|---|---:|---:|---:|---:|
| **Overall** | **85** | **39 / 46 (45.88%)** | **56 / 29 (65.88%)** | **78 / 7 (91.76%)** |
| Credit reporting | 23 | 17 / 6 (73.91%) | 19 / 4 (82.61%) | 20 / 3 (86.96%) |
| Debt collection | 12 | 10 / 2 (83.33%) | 10 / 2 (83.33%) | 12 / 0 (100.00%) |
| Mortgage | 12 | 7 / 5 (58.33%) | 8 / 4 (66.67%) | 9 / 3 (75.00%) |
| Credit card | 11 | 0 / 11 (0.00%) | 7 / 4 (63.64%) | 11 / 0 (100.00%) |
| Bank account or service | 19 | 5 / 14 (26.32%) | 10 / 9 (52.63%) | 19 / 0 (100.00%) |
| Consumer loan | 4 | 0 / 4 (0.00%) | 1 / 3 (25.00%) | 3 / 1 (75.00%) |
| Money transfer or service | 4 | 0 / 4 (0.00%) | 1 / 3 (25.00%) | 4 / 0 (100.00%) |

## Which Qwen test results set the limits?

Qwen was the top model in A1 and ran again on all 90 even source rows after tuning. The overall floor is its test accuracy minus 10 percentage points. Each category floor is its test accuracy in that category minus 15 points. Equality passes. The last column is the smallest whole-ticket count that meets the exact floor. Displayed percentages are rounded. [Frozen test rows](../data/golden_test.csv)

| True category | Test tickets | Qwen right | Qwen wrong | Qwen accuracy | A2 floor | Minimum right |
|---|---:|---:|---:|---:|---:|---:|
| **Overall** | **90** | **64** | **26** | **71.11%** | **61.11%** | **55** |
| Credit reporting | 20 | 14 | 6 | 70.00% | 55.00% | 11 |
| Debt collection | 13 | 10 | 3 | 76.92% | 61.92% | 9 |
| Mortgage | 11 | 7 | 4 | 63.64% | 48.64% | 6 |
| Credit card | 7 | 5 | 2 | 71.43% | 56.43% | 4 |
| Bank account or service | 18 | 13 | 5 | 72.22% | 57.22% | 11 |
| Consumer loan | 10 | 8 | 2 | 80.00% | 65.00% | 7 |
| Money transfer or service | 11 | 7 | 4 | 63.64% | 48.64% | 6 |

Credit card has seven test tickets. One changed answer shifts that category by 14.29 percentage points, nearly the full allowance. The frozen split reuses complaints seen in A1, so these results compare configurations on the same tickets. Performance on previously unseen complaints remains a separate question.

## Run evidence

Batch `step1-20261127T140752Z-14aa0cd1`. Each ticket went through `POST /tickets` for classification. The evaluator then asked the same model for confidence in a separate timed call. Only the evaluator had the reference label. The predictions CSV and both logs are joined by request ID.

| Split | Model | Requests | Classification errors | Confidence scores | Evidence |
|---|---|---:|---:|---:|---|
| Tuning | Llama 3.2 1B | 85 | 0 | 85/85 | [Predictions](results/step1-20261127T140752Z-14aa0cd1/tuning/llama-1b/predictions.csv) · [Scores and confusion matrix](results/step1-20261127T140752Z-14aa0cd1/tuning/llama-1b/accuracy.json) · [Ticket log](logs/step1-20261127T140752Z-14aa0cd1/tuning/llama-1b/step1-20261127T140752Z-14aa0cd1-tuning-llama-1b.tickets.jsonl) · [Service log](logs/step1-20261127T140752Z-14aa0cd1/tuning/llama-1b/step1-20261127T140752Z-14aa0cd1-tuning-llama-1b.jsonl) |
| Tuning | Llama 3.2 3B | 85 | 0 | 85/85 | [Predictions](results/step1-20261127T140752Z-14aa0cd1/tuning/llama-3b/predictions.csv) · [Scores and confusion matrix](results/step1-20261127T140752Z-14aa0cd1/tuning/llama-3b/accuracy.json) · [Ticket log](logs/step1-20261127T140752Z-14aa0cd1/tuning/llama-3b/step1-20261127T140752Z-14aa0cd1-tuning-llama-3b.tickets.jsonl) · [Service log](logs/step1-20261127T140752Z-14aa0cd1/tuning/llama-3b/step1-20261127T140752Z-14aa0cd1-tuning-llama-3b.jsonl) |
| Tuning | Qwen2.5 7B | 85 | 0 | 85/85 | [Predictions](results/step1-20261127T140752Z-14aa0cd1/tuning/qwen-7b/predictions.csv) · [Scores and confusion matrix](results/step1-20261127T140752Z-14aa0cd1/tuning/qwen-7b/accuracy.json) · [Ticket log](logs/step1-20261127T140752Z-14aa0cd1/tuning/qwen-7b/step1-20261127T140752Z-14aa0cd1-tuning-qwen-7b.tickets.jsonl) · [Service log](logs/step1-20261127T140752Z-14aa0cd1/tuning/qwen-7b/step1-20261127T140752Z-14aa0cd1-tuning-qwen-7b.jsonl) |
| Test | Qwen2.5 7B | 90 | 0 | 90/90 | [Predictions](results/step1-20261127T140752Z-14aa0cd1/test/qwen-7b/predictions.csv) · [Scores and confusion matrix](results/step1-20261127T140752Z-14aa0cd1/test/qwen-7b/accuracy.json) · [Ticket log](logs/step1-20261127T140752Z-14aa0cd1/test/qwen-7b/step1-20261127T140752Z-14aa0cd1-test-qwen-7b.tickets.jsonl) · [Service log](logs/step1-20261127T140752Z-14aa0cd1/test/qwen-7b/step1-20261127T140752Z-14aa0cd1-test-qwen-7b.jsonl) |

To repeat the sequence, run `python 1_accuracy-limits/run_step1.py` from `Assignment 2`. Each invocation saves its own batch under `results/` and `logs/`. [Runner](run_step1.py)
