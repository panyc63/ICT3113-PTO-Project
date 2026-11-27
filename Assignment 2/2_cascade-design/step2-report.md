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

## How did the two settings compare on the tuning set?

We replayed both settings on the same **85 odd-row tuning tickets**. For each row, we took Llama’s saved category when its confidence met the cutoff and Qwen’s saved category otherwise. All 85 Llama scores were available. The golden label was used only to score the resulting answer. [Tuning labels](../data/golden_tuning.csv) · [Llama predictions and confidence](../1_accuracy-limits/results/step1-20261127T140752Z-14aa0cd1/tuning/llama-3b/predictions.csv) · [Qwen predictions](../1_accuracy-limits/results/step1-20261127T140752Z-14aa0cd1/tuning/qwen-7b/predictions.csv)

| Acceptance cutoff | Llama answers accepted | Wrong among accepted | Sent to Qwen | Replay right / wrong | Tuning accuracy |
|---|---:|---:|---:|---:|---:|
| Setting 1 · ≥90% | 37 | 8/37 | 48/85 (56.47%) | 73 / 12 | 85.88% |
| Setting 2 · ≥80% | 61 | 15/61 | 24/85 (28.24%) | 69 / 16 | 81.18% |

Exactly **24 tickets** scored 80–89. Across those tickets, Qwen alone was correct on six and Llama alone was correct on two. Lowering the cutoff therefore saved **24 Qwen calls** at a cost of **four correct answers** in the replay. Bank account or service saw the largest loss, from 16/19 correct at 90% to 13/19 at 80%. The team will carry both cutoffs into the held-out test. End-to-end latency and test-set accuracy still require live cascade measurements.

## What the benchmark must capture

An accepted ticket incurs **two model calls** because Llama classifies the ticket and then rates its confidence. An escalated ticket incurs **three**, adding Qwen classification. Include the confidence call in end-to-end latency for both routes. For each ticket, log the request ID, setting and cutoff, Llama category and score, escalation decision and reason, final model and category, and each call’s duration. This lets the team check both the cost of escalation and the accuracy of accepted answers.

The saved warm-up shows Llama 3B (2.6 GB) and Qwen 7B (5.1 GB) resident together on CPU after alternating requests in one Ollama container. Confirm both appear in `ollama ps` after warm-up for each formal cascade run. [Archived memory check](https://github.com/panyc63/ICT3113-PTO-Project/blob/d40dc5d8510f65da803e5ad490edba3de73655b9/Assignment%202/results/memory-3b-7b.json)

**Implementation status.** The current API escalates by predicted category. Confidence routing inside `POST /tickets` and live measurements for these two settings are pending. [Current API](../main.py) · [Earlier category-based rule](../escalation_rule.md) · [Step 3 confidence-cascade predictions](../3_record-predictions/step3-report.md)
