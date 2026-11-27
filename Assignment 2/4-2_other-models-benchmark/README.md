# Step 4-2 — Each other Assignment 1 model alone

Evaluate `llama3.2:1b` and `llama3.2:3b` on the same 90 even-row tickets as Qwen. Each candidate handles its own tickets using the A1 classification prompt, seven categories, pinned model digest, and CPU inference settings. As in Step 4-1, a separate call to the same model records confidence after a successful classification. The reference label is used only for scoring. [Step 4-2 results](step4-2-report.md)

## Run both candidates

From `Assignment 2` on the service host, run

```powershell
python .\4-2_other-models-benchmark\run_step4_2.py
```

The 1B run finishes before the 3B run starts. To repeat just one candidate, add `--model llama3.2:1b` or `--model llama3.2:3b`. Each invocation creates a new batch and preserves earlier results.

The default reference is the A1 Qwen run rescored on the 90 frozen A2 test rows. The runner checks the Qwen tag, digest and scores against the per-ticket predictions before starting a candidate. To reproduce a comparison against a different Qwen run, pass its report with `--baseline`. [Step 1 reference](../1_accuracy-limits/a2-test-rows/accuracy.json)

## Read the results

| File inside this step | Contents |
|---|---|
| `results/<batch>/llama-1b/` and `llama-3b/` | Each model's predictions CSV and accuracy JSON with right/wrong counts, per-category accuracy, and confusion matrix. |
| `logs/<batch>/<model-folder>/<run-id>.tickets.jsonl` | Ticket narrative and row ID, reference and predicted category, confidence, timings, and errors. The model folder is `llama-1b` or `llama-3b`, as under `results/<batch>/`. |
| `logs/<batch>/<model-folder>/<run-id>.jsonl` | Service audit joined to the ticket log by request ID. |
| `results/<batch>/comparison.json` | The Qwen run ID, reference scores, floors, and each candidate's overall and per-category pass/fail decisions. |

A candidate qualifies if its overall accuracy is within 10 percentage points of Qwen and every category is within 15 points. For each qualifying single model, use the [three-run JMeter procedure](../README.md#calibrate-and-speed-test-three-runs-per-configuration) at the same calibrated arrival rate as Qwen. Those results determine which qualifying model is fastest.

## Previously saved A2 runs

The [existing comparison](../results/accuracy-comparison.json) used Qwen run `acc-qwen`, which scored 64/90 (71.11%) and set an overall floor of 61.11%.

| Candidate | Correct | Wrong | Accuracy | Outcome in that batch |
|---|---:|---:|---:|---|
| [Llama 1B](../results/acc-1b/accuracy.json) | 27 | 63 | 30.00% | Failed the overall floor and five category floors |
| [Llama 3B](../results/acc-3b/accuracy.json) | 42 | 48 | 46.67% | Failed the overall floor and five category floors |
