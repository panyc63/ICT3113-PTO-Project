# Step 2 — Design the confidence-based cascade

**Setting 1 accepts Llama’s category at 90% confidence or higher. Setting 2 accepts it at 80% or higher.** Both settings use the same self-reported confidence rule. A score at or above the selected cutoff is HIGH and Llama’s category is accepted. A lower score is LOW and the ticket goes to Qwen. The main risk is that Llama can assign high confidence to a wrong answer.

## How one ticket is routed

1. Inside `POST /tickets`, send the narrative to Llama 3.2 3B (`llama3.2:3b`) with the unchanged A1 classification prompt. Keep its predicted category.
2. Ask **the same Llama model** in a separate call how confident it is in that category for this narrative. Request one integer from 0 to 100 using the existing standalone confidence prompt. The model sees the narrative and its prediction. Only the evaluator sees the golden label. [Confidence prompt and response schema](../single_model_benchmark.py)
3. Apply the cutoff below. For an escalation, send the original narrative to Qwen2.5 7B (`qwen2.5:7b`) with the A1 classification prompt. Return one final category.

| Llama confidence | Setting 1 (90%) | Setting 2 (80%) |
|---|---|---|
| 90–100 | Accept Llama | Accept Llama |
| 80–89 | Escalate to Qwen | Accept Llama |
| 0–79 | Escalate to Qwen | Escalate to Qwen |

An absent or invalid score cannot satisfy the acceptance condition. The proposed fallback is to escalate and log the confidence error separately from a valid LOW score.

## How the two settings will be evaluated

Collect one Llama prediction and confidence score per ticket on the 85 odd-row tuning tickets. Apply both cutoffs to those same scores. Only tickets scoring **80–89** change route. Each such ticket saves one Qwen call under Setting 2. Compare Llama’s and Qwen’s answers on those tickets against the golden labels to see how the lower cutoff affects accuracy.

For each setting, count accepted tickets, wrong accepted answers and escalations. Use Qwen’s prediction on escalated rows to estimate overall and per-category cascade accuracy.

The saved odd-row files contain both models’ categories and classification timings. Llama’s tuning file has no confidence column, so confidence still needs to be collected on those rows. Freeze both settings before measuring this rule on the 90 even-row test tickets. [Tuning rows](../data/golden_tuning.csv) · [Llama tuning predictions](../results/tuning-3b/predictions.csv) · [Qwen tuning predictions](../results/tuning-7b/predictions.csv)

## What the benchmark must capture

An accepted ticket incurs **two model calls** because Llama classifies the ticket and then rates its confidence. An escalated ticket incurs **three**, adding Qwen classification. Include the confidence call in end-to-end latency for both routes. For each ticket, log the request ID, setting and cutoff, Llama category and score, escalation decision and reason, final model and category, and each call’s duration. This lets the team check both the cost of escalation and the accuracy of accepted answers.

The saved warm-up shows Llama 3B (2.6 GB) and Qwen 7B (5.1 GB) resident together on CPU after alternating requests in one Ollama container. Confirm both appear in `ollama ps` after warm-up for each formal cascade run. [Memory check](../results/memory-3b-7b.json)

**Implementation status.** The current API escalates by predicted category. The existing cascade predictions and results belong to that earlier rule. Implementing confidence routing inside `POST /tickets` and measuring the two settings are still pending. [Current API](../main.py) · [Earlier category-based rule](../escalation_rule.md) · [Earlier prediction record](../predictions.md)
