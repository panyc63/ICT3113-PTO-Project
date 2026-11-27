# Step 4-2 — Each other Assignment 1 model alone

Evaluate `llama3.2:1b` and `llama3.2:3b` on the same 90 even-row tickets as Qwen. Each candidate handles its own tickets using the A1 classification prompt, seven categories, pinned model digest, and CPU inference settings. As in Step 4-1, a separate call to the same model records confidence after a successful classification. The reference label is used only for scoring. [Step 4-2 status](step4-2-report.md)

## Run both candidates

From `Assignment 2` on the service host, run

```powershell
python .\4-2_other-models-benchmark\run_step4_2.py
```

The 1B run finishes before the 3B run starts. To repeat just one candidate, add `--model llama3.2:1b` or `--model llama3.2:3b`. Each invocation creates a new batch and preserves earlier results.

The default reference is the latest completed Step 1 Qwen run on the 90 even-row test tickets. The runner checks the Qwen tag, digest and scores against the per-ticket predictions before starting a candidate. To select a specific report, pass it with `--baseline`. [Step 1 reference](../1_accuracy-limits/step1-report.md)

## Read the results

| File inside this step | Contents |
|---|---|
| `results/<batch>/llama-1b/` and `llama-3b/` | Each model's predictions CSV and accuracy JSON with right/wrong counts, per-category accuracy, and confusion matrix. |
| `logs/<batch>/<model-folder>/<run-id>.tickets.jsonl` | Ticket narrative and row ID, reference and predicted category, confidence, timings, and errors. The model folder is `llama-1b` or `llama-3b`, as under `results/<batch>/`. |
| `logs/<batch>/<model-folder>/<run-id>.jsonl` | Service audit joined to the ticket log by request ID. |
| `results/<batch>/comparison.json` | The Qwen run ID, reference scores, floors, and each candidate's overall and per-category pass/fail decisions. |

A candidate qualifies if its overall accuracy is within 10 percentage points of Qwen and every category is within 15 points. For each qualifying single model, use the [three-run JMeter procedure](../README.md#calibrate-and-speed-test-three-runs-per-configuration) at the same calibrated arrival rate as Qwen. Those results determine which qualifying model is fastest.
