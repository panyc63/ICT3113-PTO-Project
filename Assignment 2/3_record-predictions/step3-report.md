# Step 3 — Predictions for the confidence cascade

**Group P2-11 predicts that the 90% setting will be the fastest configuration that meets all eight accuracy limits.** At this cutoff, Llama 3B keeps its most confident answers and sends the rest to Qwen 7B. We expect the 80% setting to finish faster, but accepting Llama’s answers in the 80–89 band may cause enough additional errors to miss the overall floor. Both settings pay for a separate Llama confidence call on every successfully classified ticket. [Cascade design](../2_cascade-design/step2-report.md) · [Accuracy limits](../1_accuracy-limits/step1-report.md)

| Team forecast | Setting 1 · accept at ≥90 | Setting 2 · accept at ≥80 |
|---|---:|---:|
| Fraction sent to Qwen | 50% (about 45 of 90 test tickets) | 20% (about 18 of 90) |
| Overall accuracy | At least 60% (54 or more correct) | At risk of falling below 60% (53 or fewer if it fails) |
| Per-category qualification | Expected to pass all seven floors | Uncertain, especially in the categories below |
| Estimated median ticket latency | **6.24 s** | **5.31 s** |

These escalation and accuracy figures are team predictions. With the same tickets and confidence scores, they imply about 27 tickets in the 80–89 band that Setting 2 accepts and Setting 1 escalates. Whether those 27 decisions help or hurt depends on which model would have answered each one correctly. To win, Setting 1 must also beat Qwen alone on measured median latency. If Setting 2 meets all the floors and is faster, the team’s predicted winner is wrong.

## Deriving the median latency from A1

We paired the two archived A1 prediction files by source row and used only the **85 odd tuning rows**. Both models returned successful responses on all 85. Their median end-to-end classification times were **2.493 s for Llama** and **2.813 s for Qwen**. A1 did not measure the separate confidence call. For the forecast, we assume that asking Llama for confidence takes as long as its classification on the same ticket. [A1 Llama predictions](https://github.com/panyc63/ICT3113-PTO-Project/blob/5815a0bcf4d5fbb8131163b6db3771b51641fa2b/results/folder_name/predictions.csv) · [A1 Qwen predictions](https://github.com/panyc63/ICT3113-PTO-Project/blob/7c59787277e35af70c3525283b30bd243d810ef9/results/qwen25-7b-accuracy-01/predictions.csv) · [Frozen tuning rows](../data/golden_tuning.csv)

For each ticket, let `L` and `Q` be the A1 `elapsed_ms` for Llama and Qwen on that row. The estimated time is `2L` if accepted and `2L + Q` if escalated. Because A1 recorded no confidence scores, the model assigns every row the same chance of escalation, independent of its timing.

- **Setting 1 (50% escalation).** Give each row one accepted time and one escalated time. The median of these 170 weighted observations is **6.24 s**.
- **Setting 2 (20% escalation).** Give each row four copies of its accepted time and one of its escalated time. The median of these 425 weighted observations is **5.31 s**.

If the confidence call takes half a classification call, the estimated medians fall to **4.89 s** and **4.01 s**. The A1 sequential-ticket evidence favours Qwen alone at **2.81 s**. Under A1’s lowest JMeter load (52.44 POSTs/hour plus search traffic), the submitted A1 report (`Group11.pdf`, page 9) gave POST medians of **1.552 s for Llama** and **11.316 s for Qwen**. That larger gap under load is why a cascade win remains plausible. Step 4 will measure both settings and Qwen alone at the same arrival rate.

## Which categories are most likely to lose accuracy?

**Bank account or service is the strongest prediction.** On the 19 A1 tuning tickets with that true label, Qwen got all 19 right and Llama got nine right. If a wrong Llama answer is accepted on any of the other ten, the cascade loses a correct Qwen answer. Llama sent four of those ten to Credit reporting, four to Debt collection and two to Credit card.

| True category | Llama right / total | Qwen right / total | Qwen advantage |
|---|---:|---:|---:|
| Bank account or service | 9/19 (47.37%) | 19/19 (100%) | 52.63 percentage points |
| Consumer loan | 1/4 (25%) | 3/4 (75%) | 50.00 percentage points |
| Money transfer or service | 2/4 (50%) | 4/4 (100%) | 50.00 percentage points |
| Credit card | 6/11 (54.55%) | 11/11 (100%) | 45.45 percentage points |

Consumer loan and Money transfer or service each have only four tuning tickets, so one answer shifts their accuracy by 25 percentage points. Credit card has a slightly smaller gap with more evidence. We expect the 80% setting to expose more of these weaknesses. A1 identifies where Llama made errors, while the confidence-cascade test will show which of those types of errors it accepts.

**Timing of this record.** These forecasts were recorded after the A2 standalone benchmarks and before testing the confidence cascade. The earlier committed predictions and cascade measurements used the category-based rule. This record applies to the confidence design. [Earlier prediction record](https://github.com/panyc63/ICT3113-PTO-Project/blob/46093f50ea24733f499a46e4573f36bc63251517/Assignment%202/predictions.md)
