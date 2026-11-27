# Step 4-2 — Test each other Assignment 1 model alone

**Neither smaller model qualifies for standalone deployment.** On the same 90 test tickets, Llama 3.2 1B scored **32/90** (58 wrong, **35.56%**) and Llama 3.2 3B scored **42/90** (48 wrong, **46.67%**). The A1-derived Step 1 reference scored 63/90 (27 wrong, 70.00%). A candidate needs at least **54/90** correct overall and a pass in **all seven categories**. Llama 1B fell 22 correct answers short of the overall minimum and passed two categories. Llama 3B fell 12 short and passed four. [Step 1 reference](../1_accuracy-limits/step1-report.md) · [Comparison against Step 1](results/step2-20261127T125523Z-624d7491/comparison-step1.json)

## How did each model perform by category?

Each row groups tickets by their frozen reference label. The minimum is the smallest number of correct answers that meets the exact Qwen-derived floor. Percentages are rounded for display.

| True category | Floor | Minimum right | Llama 1B | 1B result | Llama 3B | 3B result |
|---|---:|---:|---|---|---|---|
| Overall | 60.00% | 54/90 | 32 right, 58 wrong (35.56%) | Fail | 42 right, 48 wrong (46.67%) | Fail |
| Credit reporting | 55.00% | 11/20 | 16 right, 4 wrong (80.00%) | Pass | 16 right, 4 wrong (80.00%) | Pass |
| Debt collection | 61.92% | 9/13 | 10 right, 3 wrong (76.92%) | Pass | 9 right, 4 wrong (69.23%) | Pass |
| Mortgage | 48.64% | 6/11 | 3 right, 8 wrong (27.27%) | Fail | 6 right, 5 wrong (54.55%) | Pass |
| Credit card | 42.14% | 3/7 | 0 right, 7 wrong (0.00%) | Fail | 4 right, 3 wrong (57.14%) | Pass |
| Bank account or service | 57.22% | 11/18 | 2 right, 16 wrong (11.11%) | Fail | 7 right, 11 wrong (38.89%) | Fail |
| Consumer loan | 65.00% | 7/10 | 0 right, 10 wrong (0.00%) | Fail | 0 right, 10 wrong (0.00%) | Fail |
| Money transfer or service | 48.64% | 6/11 | 1 right, 10 wrong (9.09%) | Fail | 0 right, 11 wrong (0.00%) | Fail |

Both models missed every consumer loan ticket. Llama 1B labelled the ten tickets as credit reporting (six) or debt collection (four). Llama 3B labelled them as credit reporting (five), debt collection (three), or mortgage (two). Llama 3B did meet the mortgage and credit card floors, although the credit card result rests on just seven tickets. One changed answer moves accuracy in that category by 14.29 percentage points. [1B confusion matrix](results/step2-20261127T125523Z-624d7491/llama-1b/accuracy.json) · [3B confusion matrix](results/step2-20261127T125523Z-624d7491/llama-3b/accuracy.json)

## How were the runs scored?

The original batch compared these predictions with the fresh Qwen run (62/90). The table above rescores the same saved results against the archived A1 reference. [Original batch comparison](results/step2-20261127T125523Z-624d7491/comparison.json)

On 27 November 2026, each pinned A1 candidate (`llama3.2:1b` and `llama3.2:3b`) ran alone using the A1 classification prompt. Each model classified the same 90 even-row tickets through `POST /tickets`. All 180 classifications succeeded. A separate call asked the same model for its confidence after each prediction. All 180 confidence scores were recorded. Only the match between the prediction and the frozen label counted toward accuracy. The request ID links each prediction to its ticket and service log. [Frozen test labels](../data/golden_test.csv) · [1B predictions](results/step2-20261127T125523Z-624d7491/llama-1b/predictions.csv) · [1B logs](logs/step2-20261127T125523Z-624d7491/llama-1b/) · [3B predictions](results/step2-20261127T125523Z-624d7491/llama-3b/predictions.csv) · [3B logs](logs/step2-20261127T125523Z-624d7491/llama-3b/)

## What does this mean for speed testing?

The worksheet requires standalone speed tests only for models that pass both accuracy limits. Qwen is the only qualifying standalone model, so it proceeds to the calibrated three-run JMeter benchmark. Both cascade settings still require their own accuracy and speed measurements if the model pair fits in memory. Which configuration is fastest remains open until those measurements are available.
