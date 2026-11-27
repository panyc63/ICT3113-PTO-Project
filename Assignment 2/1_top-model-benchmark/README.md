# Step 1 — Top model alone

Group 11's most accurate Assignment 1 model was **Qwen2.5 7B**. It classified **140 of 175** golden tickets correctly (80.0%). Assignment 2 sets its accuracy limits using the **90 even-row test tickets**.

## Run Qwen on the test tickets

On the service host, start Docker Desktop and use a Python environment with the A2 requirements installed. From `Assignment 2`, run

```powershell
python .\1_top-model-benchmark\run_step1.py
```

The runner starts the project's Qwen-only service and submits each test narrative to `POST /tickets`. After a successful prediction, it asks Qwen separately to rate its confidence in that category from 0 to 100. Only the evaluator reads the reference label. Classification and confidence timings are recorded separately.

Each run gets a unique ID and writes these files inside this folder.

| Output | Contents |
|---|---|
| `results/<run-id>/predictions.csv` | One row per ticket with its source row, request ID, reference and predicted categories, confidence, timings, and errors. |
| `results/<run-id>/accuracy.json` | Overall and per-category scores, confusion matrix, accuracy floors, and confidence coverage. Written when all 90 tickets finish. |
| `logs/<run-id>/<run-id>.tickets.jsonl` | One JSON object per ticket with the full narrative, `actual_category`, `predicted_category`, and `confidence`. The request ID links the entry to the service audit. |
| `logs/<run-id>/<run-id>.jsonl` | Raw triage service audit, including Qwen's classification call and its duration. |

Confidence is Qwen's self-reported score. If the confidence call fails, the log records a null score and the reason, and the classification still counts. If classification fails, the ticket counts as incorrect and confidence is skipped. The separate confidence call is specific to this accuracy runner. Use the shared JMeter procedure for A2 speed measurements.

## Benchmark files

- [a1-run/](a1-run/) contains the original predictions, accuracy report, run metadata, service log, and CPU/GPU captures for `qwen25-7b-accuracy-01`. These files come from the [archived A1 run](https://github.com/panyc63/ICT3113-PTO-Project/tree/7c59787277e35af70c3525283b30bd243d810ef9/results/qwen25-7b-accuracy-01) and its [service log](https://github.com/panyc63/ICT3113-PTO-Project/blob/7c59787277e35af70c3525283b30bd243d810ef9/logs/qwen25-7b-accuracy-01.jsonl).
- [a2-test-rows/predictions.csv](a2-test-rows/predictions.csv) contains the A1 predictions matching the [frozen A2 test rows](../data/golden_test.csv). Each row retains its original request ID so it can be checked against the service log.
- [a2-test-rows/accuracy.json](a2-test-rows/accuracy.json) contains the resulting counts, confusion matrix, and accuracy floors. The timing fields in the CSV come from the A1 accuracy run. A2 speed measurements use a separate, calibrated JMeter run.

## Accuracy limits from the saved predictions

The overall floor is Qwen's even-row accuracy minus 10 percentage points. Each category floor is Qwen's accuracy for that category minus 15 points. The figures below are rounded for display.

| Test rows | Right | Wrong | Qwen accuracy | A2 floor if reused |
|---|---:|---:|---:|---:|
| **Overall** | **63** | **27** | **70.00%** | **60.00%** |
| Credit reporting | 14 | 6 | 70.00% | 55.00% |
| Debt collection | 10 | 3 | 76.92% | 61.92% |
| Mortgage | 7 | 4 | 63.64% | 48.64% |
| Credit card | 4 | 3 | 57.14% | 42.14% |
| Bank account or service | 13 | 5 | 72.22% | 57.22% |
| Consumer loan | 8 | 2 | 80.00% | 65.00% |
| Money transfer or service | 7 | 4 | 63.64% | 48.64% |

Credit card has only seven test tickets. One additional error changes its score by 14.29 percentage points.

**Formal reuse is pending.** The A1 and A2 model digests match. The brief also requires the same classification prompt, Ollama version, and machine. The saved setup evidence leaves the A1 Ollama version and machine identity unconfirmed. If those conditions cannot be established, run Qwen alone on the same 90 tickets under the A2 setup and derive the floors from that run. [A2 environment record](../docs/environment.md)
