# Step 1 — Define the accuracy limits from Assignment 1

**A configuration needs at least 54 of the 90 test tickets correct and must meet all seven category floors.** Group 11’s top A1 model, Qwen2.5 7B, scored 140 right and 35 wrong on the full golden set (80.00%). Filtering its archived predictions to the frozen A2 test rows gives **63 right and 27 wrong (70.00%)**. Subtracting 10 percentage points gives the **60.00% overall floor**. Each category floor is its own Qwen score minus 15 percentage points. Equality passes, using unrounded values.

| True category | Test tickets | A1 Qwen right | Wrong | Accuracy | A2 floor | Minimum right |
|---|---:|---:|---:|---:|---:|---:|
| **Overall** | **90** | **63** | **27** | **70.00%** | **60.00%** | **54** |
| Credit reporting | 20 | 14 | 6 | 70.00% | 55.00% | 11 |
| Debt collection | 13 | 10 | 3 | 76.92% | 61.92% | 9 |
| Mortgage | 11 | 7 | 4 | 63.64% | 48.64% | 6 |
| Credit card | 7 | 4 | 3 | 57.14% | 42.14% | 3 |
| Bank account or service | 18 | 13 | 5 | 72.22% | 57.22% | 11 |
| Consumer loan | 10 | 8 | 2 | 80.00% | 65.00% | 7 |
| Money transfer or service | 11 | 7 | 4 | 63.64% | 48.64% | 6 |

The team sorted the 175 original source row IDs and committed the split. The 85 odd rows are for tuning. The 90 even rows are for comparing configurations. All tickets had already been seen in A1. Credit card has just seven test tickets, so changing one answer moves its score by 14.29 percentage points, almost the full category allowance. [Frozen tuning rows](../data/golden_tuning.csv) · [Frozen test rows](../data/golden_test.csv) · [Split commit](https://github.com/panyc63/ICT3113-PTO-Project/commit/998344b1d946a28b9fed7f5f796cf421fdd96dcf)

## Source and reuse conditions

The reference run is `qwen25-7b-accuracy-01`. The even-row extract retains each original request ID so a prediction can be traced to the A1 service log. The model digest and classification prompt match A2. Formal reuse under the worksheet still requires confirmation that the archived A1 benchmark used the same machine and Ollama version as A2. The separate Step 4-1 report records the fresh A2 measurement. [Original A1 run in Git](https://github.com/panyc63/ICT3113-PTO-Project/tree/7c59787277e35af70c3525283b30bd243d810ef9/results/qwen25-7b-accuracy-01) · [A1 run metadata](a1-run/metadata.json) · [A1 service log](a1-run/qwen25-7b-accuracy-01.jsonl) · [A2 environment record](../docs/environment.md) · [Step 4-1 Qwen report](../4-1_top-model-benchmark/step4-1-report.md)

To reproduce the accuracy counts offline, run the following from `Assignment 2` with an unused output filename. The scorer reads all 175 original predictions and selects the frozen test rows. [Archived predictions](a1-run/predictions.csv) · [Even-row extract](a2-test-rows/predictions.csv) · [Scores, confusion matrix and floors](a2-test-rows/accuracy.json)

```powershell
python accuracy.py score --split test --predictions 1_accuracy-limits/a1-run/predictions.csv --output results/step1-recomputed.json
```
