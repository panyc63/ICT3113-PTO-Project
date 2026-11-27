# Step 4-1 — Held-out accuracy tests

We used the same 90 even-row tickets and golden labels for Qwen alone and both cascades. Qwen’s standalone Step 1 run scored **64/90 (71.11%)**. A candidate qualifies by getting at least **55/90** correct overall and meeting the floor in **each of seven categories**. The comparisons use full precision. [Frozen test rows](../data/golden_test.csv) · [Qwen’s Step 1 accuracy and floors](../1_accuracy-limits/results/step1-20261127T140752Z-14aa0cd1/test/qwen-7b/accuracy.json)

## Which settings met the limits?

**Qwen alone qualified. Both cascades reached the overall floor, but each fell below the required accuracy for Consumer loan and Money transfer or service.** The 90% setting also missed the Credit card floor. The standalone Llama test runs are still pending. [Qualification comparison](results/step4-20261127T151441Z-7403c863/comparison.json)

| Configuration | Right / wrong | Accuracy | Sent to Qwen | Median per ticket | Time for 90 tickets | All limits met? |
|---|---:|---:|---:|---:|---:|---|
| Qwen 7B alone, Step 1 | 64 / 26 | 71.11% | — | 5.78 s | — | Yes |
| Llama 3B → Qwen 7B at 90% | 56 / 34 | 62.22% | 47/90 (52.22%) | 6.06 s | 11 min 50 s | No |
| Llama 3B → Qwen 7B at 80% | 55 / 35 | 61.11% | 34/90 (37.78%) | 5.20 s | 10 min 02 s | No |

Qwen’s median uses the Step 1 classification request time. Its separate confidence call was collected for analysis and sits outside that request. Both cascade medians include Llama’s confidence call because the API needs the score before it can answer. [Qwen classification timings](../1_accuracy-limits/results/step1-20261127T140752Z-14aa0cd1/test/qwen-7b/predictions.csv) · [90% timings](results/step4-20261127T151441Z-7403c863/setting-1-90/predictions.csv) · [80% timings](results/step4-20261127T151441Z-7403c863/setting-2-80/predictions.csv)

### Category limits

Each result shows correct tickets out of all tickets with that golden category. Bold entries fell below the exact floor. [90% scores and confusion matrix](results/step4-20261127T151441Z-7403c863/setting-1-90/accuracy.json) · [80% scores and confusion matrix](results/step4-20261127T151441Z-7403c863/setting-2-80/accuracy.json)

| Golden category | Accuracy floor | Minimum correct | Qwen alone | 90% setting | 80% setting |
|---|---:|---:|---:|---:|---:|
| Credit reporting | 55.00% | 11 | 14/20 | 16/20 | 16/20 |
| Debt collection | 61.92% | 9 | 10/13 | 10/13 | 9/13 |
| Mortgage | 48.64% | 6 | 7/11 | 7/11 | 7/11 |
| Credit card | 56.43% | 4 | 5/7 | **2/7** | 4/7 |
| Bank account or service | 57.22% | 11 | 13/18 | 11/18 | 13/18 |
| Consumer loan | 65.00% | 7 | 8/10 | **5/10** | **1/10** |
| Money transfer or service | 48.64% | 6 | 7/11 | **5/11** | **5/11** |

At 90%, Llama answered 43 tickets itself and got 24 right. Qwen got 32 of the 47 escalations right. At 80%, Llama answered 56 and got 32 right, while Qwen got 23 of 34 escalations right. A high self-reported score still accepted 19 wrong answers at 90% and 24 at 80%. Across both runs, all 180 tickets received a valid confidence score and a final category. [90% ticket audit](logs/step4-20261127T151441Z-7403c863/setting-1-90/step4-20261127T151441Z-7403c863-setting-1-90.tickets.jsonl) · [80% ticket audit](logs/step4-20261127T151441Z-7403c863/setting-2-80/step4-20261127T151441Z-7403c863-setting-2-80.tickets.jsonl)

## Measurement

Llama 3B classified each narrative, then rated its own prediction in a separate call. A score at or above the setting’s cutoff accepted Llama’s category. A lower or unavailable score sent the original narrative to Qwen 7B for the final category. Each setting made fresh model calls for every ticket. The gold category was available only to the evaluator. [Frozen confidence rule](../2_cascade-design/step2-report.md)

We submitted one ticket at a time after warming both models on three non-golden tickets. Client elapsed time covers the complete HTTP request, including classification, the confidence call, any Qwen escalation, and the API response. The batch time covers the 90-ticket measurement loop and excludes setup and warm-up. These timings describe the accuracy workload. Formal speed testing is a later stage.

Before each test, Ollama showed Llama 3B (2.6 GB) and Qwen 7B (5.1 GB) resident together on CPU. The existing Llama 1B was also resident and received zero benchmark calls. [90% residency check](results/step4-20261127T151441Z-7403c863/setting-1-90/residency.json) · [80% residency check](results/step4-20261127T151441Z-7403c863/setting-2-80/residency.json)

## Reproduce

From the `Assignment 2` directory, run:

```powershell
python 4-1_accuracy-tests/run_step4_1.py
```

Each batch gets a new directory under `results/` and `logs/`. Each setting saves its predictions, latency, accuracy, confusion matrix and CPU residency evidence. Its paired logs contain the API audit and a ticket-by-ticket record with the narrative, gold and final categories, Llama’s category and confidence, routing decision, and call durations. [Accuracy runner](run_step4_1.py)
