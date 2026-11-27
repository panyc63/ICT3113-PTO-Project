# Escalation rule — Group P2-11

The team selected Llama 3B’s self-reported confidence. Llama classifies each ticket and rates its prediction in a second call. Setting 1 accepts a score of at least 90 and Setting 2 accepts a score of at least 80. Lower or unavailable scores send the ticket to Qwen 7B. [Step 2 rule and tuning evidence](2_cascade-design/step2-report.md)

## Earlier category-based cascade

The two settings were selected using the 85 odd source rows in the frozen tuning set. Use the exact Assignment 1 prompt and category schema for every call. Both models must remain resident on the Assignment 1 CPU-only machine with the original CPU and RAM allocation.

1. Classify each ticket with the smaller model.
2. If its valid predicted category belongs to the setting's acceptance list, accept it. The true category is never available to the rule.
3. Otherwise classify the same narrative with the larger model and use that answer. A malformed small-model category also escalates. Transport failures/timeouts are reported as errors rather than silently replaced by an answer.
4. Store exactly one final result and keep the public POST response unchanged. Log the initial prediction, escalation flag and reason, per-model durations, model identities and final answer.

**Selected pair.** Llama 3.2 3B (`llama3.2:3b`) classifies first. Qwen 2.5 7B (`qwen2.5:7b`) gives the final answer when a ticket is escalated.

| Setting | Accept Llama predictions in these categories | Accepted | Escalated | Estimated tuning accuracy |
|---|---|---:|---:|---:|
| 1 — conservative | Mortgage | 11/85 (12.94%) | 74/85 (87.06%) | 80/85 (94.12%) |
| 2 — aggressive | Mortgage, Credit card, Bank account or service | 30/85 (35.29%) | 55/85 (64.71%) | 76/85 (89.41%) |

Use `--accept-categories 'Mortgage'` for Setting 1 and `--accept-categories 'Mortgage|Credit card|Bank account or service'` for Setting 2 when launching the cascade.

## Tuning evidence

| Llama's predicted category | Correct / predicted | Precision | Accepted in |
|---|---:|---:|---|
| Credit reporting | 21/30 | 70.00% | Neither setting |
| Debt collection | 10/23 | 43.48% | Neither setting |
| Mortgage | 11/11 | 100.00% | Both settings |
| Credit card | 7/9 | 77.78% | Setting 2 |
| Bank account or service | 8/10 | 80.00% | Setting 2 |
| Consumer loan | 1/1 | 100.00% | Neither setting |
| Money transfer or service | 1/1 | 100.00% | Neither setting |

Mortgage had all 11 predictions correct and corrected two Qwen errors in the paired replay. Consumer loan and Money transfer or service each had only one Llama prediction, so both settings escalate those labels. The aggressive setting adds two categories with nine or more predictions each. It avoids 19 additional Qwen calls on tuning and incurs four false acceptances.

Of the four false acceptances in Setting 2, two actual Bank account or service tickets were predicted as Credit card. One actual Debt collection ticket and one actual Credit reporting ticket were both predicted as Bank account or service. This is why evaluation checks accuracy by the **true category**, while routing uses the **predicted category**. In the paired replay, the largest true-category drop from Qwen alone was 10.53 percentage points for Bank account or service. Setting 1 had zero false acceptances.

The replay pairs `results/tuning-3b/predictions.csv` and `results/tuning-7b/predictions.csv` by source row. All 85 requests succeeded in each single-model run. Confirm the predictions on the 90 held-out tickets and measure both settings under JMeter load.

## Memory check

`results/memory-3b-7b.json` records both models loaded simultaneously after interleaved warm-up, with 2.6 GB for Llama 3B and 5.1 GB for Qwen 7B. Both ran at 100% CPU with zero VRAM reported. Verify residency again during the formal cascade runs.

Freeze and commit the final rule before held-out evaluation. Do not choose a different list after inspecting the even-row scores.
