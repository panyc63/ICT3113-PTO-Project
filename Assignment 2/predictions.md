# Assignment 2 predictions — Group P2-11

The current Step 3 record covers the **90% and 80% self-reported confidence settings**. It contains the team's forecasts, the A1 latency derivation and the categories expected to lose accuracy. [Confidence cascade predictions](3_record-predictions/step3-report.md)

## Earlier predictions for the category-based cascade

These predictions use the 85-ticket tuning runs for Llama 3.2 3B and Qwen 2.5 7B. Both runs used the odd source rows from the frozen split. The 90 held-out tickets are reserved for the formal accuracy tests.

- **Expected fastest qualifying configuration.** Qwen 2.5 7B alone. It scored 78/85 (91.76%) on tuning with a 6.49 s median request time. Llama 3.2 3B alone had a faster 2.80 s median, but its 59/85 (69.41%) tuning score was 22.35 percentage points below Qwen's. Both cascade settings send a majority of tickets to Qwen after a Llama call, so their predicted medians are higher than Qwen's. Llama 3.2 1B is expected to fall below the accuracy limits given its reported 38.9% accuracy in Assignment 1. Its qualification still needs to be checked on the held-out set.
- **Cascade pair.** `llama3.2:3b` classifies first and `qwen2.5:7b` handles escalated tickets. The warm-up evidence in `results/memory-3b-7b.json` shows both models resident simultaneously on CPU.

| Cascade setting | Expected escalation fraction | Expected test accuracy | Expected median latency | Rationale |
|---|---:|---:|---:|---|
| 1 (conservative) | 87.06% (74/85 on tuning) | About 94% (80/85 on tuning) | About 8.82 s | Accepting Mortgage alone kept 11 correct Llama answers, including two tickets Qwen misclassified. The other 74 tickets incurred both calls. |
| 2 (aggressive) | 64.71% (55/85 on tuning) | About 89% (76/85 on tuning) | About 7.00 s | Adding Credit card and Bank account or service accepted 19 more Llama answers, four of which were incorrect. The lower escalation rate is expected to reduce the median relative to Setting 1. |

**Expected category losses.** Setting 1 had zero false acceptances among 11 Mortgage predictions. Setting 2's largest tuning drop was for actual Bank account or service tickets, from 19/19 with Qwen alone to 17/19 (−10.53 percentage points). Llama labelled two of these tickets as Credit card. The other drops came from one actual Debt collection ticket (12/12 to 11/12) and one actual Credit reporting ticket (20/23 to 19/23), both labelled Bank account or service by Llama. These three actual categories are the ones most likely to lose accuracy under Setting 2.

For each tuning row, the accuracy estimate selects the recorded Llama or Qwen prediction according to the rule. The latency estimate uses Llama's `elapsed_ms` for accepted rows and adds that row's separately measured Qwen `elapsed_ms` for escalated rows. Each estimate is the median of the resulting per-ticket times. These are forecasts from sequential requests. Held-out accuracy and JMeter latency can differ with the workload and queueing.

Sources are `results/tuning-3b/predictions.csv` and `results/tuning-7b/predictions.csv`. The formal accuracy limits will be calculated from Qwen's score on the 90 held-out tickets.

Predictions are not revised after the first formal measurement. Record the prediction commit hash in the final presentation.
