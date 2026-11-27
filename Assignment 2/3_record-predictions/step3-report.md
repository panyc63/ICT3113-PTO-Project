# Step 3 — Predictions for the confidence cascade

**We predict Qwen 7B alone will be the fastest configuration that meets all accuracy limits.** On the 85 odd-row tuning tickets, Qwen got 78/85 correct (91.76%) with a median classification time of 6.05 s. Both cascade settings had higher estimated median latency. Llama 1B alone fell below the overall floor on tuning, and Llama 3B alone fell below three category floors. Step 1 sets the qualification criteria at 55/90 correct (61.11%) overall and a separate minimum for each of the seven categories. [Step 1 model results and accuracy limits](../1_accuracy-limits/step1-report.md)

## What do we expect at each confidence cutoff?

The estimates use the Step 2 replay. Llama 3B classifies the ticket and rates its own prediction. At or above the cutoff, the cascade accepts Llama’s answer. Below the cutoff, Qwen 7B classifies the ticket. Both replays cleared the overall and category floors on tuning, so we expect both settings to qualify, with greater risk of a category failure at 80%. [Step 2 rule and tuning replay](../2_cascade-design/step2-report.md)

| Llama acceptance cutoff | Estimated fraction sent to Qwen | Estimated overall accuracy | Estimated median ticket time |
|---|---:|---:|---:|
| Setting 1 · ≥90% | 48/85 (56.47%) | 73/85 (85.88%) | 8.94 s |
| Setting 2 · ≥80% | 24/85 (28.24%) | 69/85 (81.18%) | 6.85 s |

For each tuning ticket, we added Llama’s recorded classification and confidence-call times. We added Qwen’s classification time only when the score fell below the cutoff, then took the median of the 85 ticket totals. On tuning, the 80% cutoff saved 24 Qwen calls and reduced estimated median latency by 2.10 s, at a cost of four correct answers. The timings come from separate standalone runs. [Llama tuning predictions and timings](../1_accuracy-limits/results/step1-20261127T140752Z-14aa0cd1/tuning/llama-3b/predictions.csv) · [Qwen tuning predictions and timings](../1_accuracy-limits/results/step1-20261127T140752Z-14aa0cd1/tuning/qwen-7b/predictions.csv)

## Which categories are most likely to lose accuracy?

**Bank account or service is the clearest risk at both cutoffs.** Qwen got 19/19 right on tuning. The cascade got 16/19 at 90% and 13/19 at 80%. Credit card showed the next largest loss at 80%, falling from 11/11 with Qwen to 8/11, compared with 10/11 at 90%.

Consumer loan stayed at 3/4 for all three configurations. Money transfer or service went from 4/4 with Qwen and the 90% cascade to 3/4 at 80%. Each category has only four tuning tickets, so one answer changes its estimated accuracy by 25 percentage points. [Step 1 category counts](../1_accuracy-limits/step1-report.md) · [Step 2 cascade design](../2_cascade-design/step2-report.md)
