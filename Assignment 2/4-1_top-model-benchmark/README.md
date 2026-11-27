# Step 4-1 — Top model alone

This benchmark measures Qwen2.5 7B alone on the 90 even-row A2 test tickets. The saved run scored 62/90 and passes the A1-derived limits. [Step 4-1 results](step4-1-report.md) · [Step 1 accuracy limits and A1 evidence](../1_accuracy-limits/step1-report.md)

## Run Qwen on the test tickets

On the service host, start Docker Desktop and use a Python environment with the A2 requirements installed. From `Assignment 2`, run

```powershell
python .\4-1_top-model-benchmark\run_step4_1.py
```

The runner starts the project's Qwen-only service and submits each test narrative to `POST /tickets`. After a successful prediction, it asks Qwen separately to rate its confidence in that category from 0 to 100. Only the evaluator reads the reference label. Classification and confidence timings are recorded separately.

Each run gets a unique ID and writes these files inside this folder.

| Output | Contents |
|---|---|
| `results/<run-id>/predictions.csv` | One row per ticket with its source row, request ID, reference and predicted categories, confidence, timings, and errors. |
| `results/<run-id>/accuracy.json` | Overall and per-category scores, confusion matrix, floors implied by this specific run, and confidence coverage. Written when all 90 tickets finish. |
| `logs/<run-id>/<run-id>.tickets.jsonl` | One JSON object per ticket with the full narrative, `actual_category`, `predicted_category`, and `confidence`. The request ID links the entry to the service audit. |
| `logs/<run-id>/<run-id>.jsonl` | Raw triage service audit, including Qwen's classification call and its duration. |

Confidence is Qwen's self-reported score. If the confidence call fails, the log records a null score and the reason, and the classification still counts. If classification fails, the ticket counts as incorrect and confidence is skipped. The separate confidence call is specific to this accuracy runner. Use the shared JMeter procedure for A2 speed measurements.
