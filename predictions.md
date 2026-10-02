# Team P2-11 Prediction Record
Status: This record must not be represented as prediction of actual runs. Estimates below were selected without reading their accuracy scores. Preserve earlier records and run history when explaining the sequence of work.

## Test conditions

Use the same test environment for all candidates. The numerical estimates below are provisional expectations for comparison, not calibrated performance guarantees.

Inference uses local CPU-only Ollama. Requests are synchronous, with no application cache or application queue. Ollama is configured with one parallel inference slot. Use a separate machine for the load generator in reported testing.

## Expected bottleneck

We expect CPU inference in Ollama to be the primary bottleneck. Processing the narrative and generating a category should cost more than inserting one SQLite row or serialising a small HTTP response.

For successful warmed-up single requests, we predict Ollama's reported total duration will account for more than 80% of the service request duration. Under sustained arrivals above the model's processing capacity, we predict increasing outstanding requests, rising p95 response times and eventually timeouts. We expect larger models to reach this limit at lower arrival rates. These claims should be checked against backend timings, service logs and open-loop JMeter results.

## Predictions by candidate model

The proposed candidates are `llama3.2:1b`, `llama3.2:3b` and `qwen2.5:7b`. Only the first is currently verified as installed. The 1B and 3B Llama models allow a within-family comparison; Qwen adds a larger size class and a different family. Family and quantisation also vary, so any differences cannot be attributed to parameter count alone.

Accuracy is the percentage of the 175 final reference-labelled tickets classified correctly; invalid outputs and failed requests count as incorrect. These are subjective starting estimates, not published results for this dataset or performance guarantees. If the reference labels are simulated, describe the measured outcome as agreement with simulated labels rather than validated human-ground-truth accuracy.

Latency means the median full POST /tickets response time with one outstanding request at a time, after the model has loaded, using the same prompt and output format across candidates. Separate cold-start latency from these estimates.

| Exact model tag | Expected accuracy | Expected median latency |
|---|---:|---:|
| llama3.2:1b | 65% | 3 seconds |
| llama3.2:3b | 75% | 7 seconds |
| qwen2.5:7b | 80% | 15 seconds |

We expect the 1B candidate to be fastest but more prone to confusing the product mentioned with the main complaint. We predict the 3B candidate will improve accuracy by 10 percentage points at a cost of more than twice the median latency. We predict a further 5-point improvement from the 7B candidate, with roughly twice the 3B latency. These increments are deliberately testable hypotheses; they are not inferred from completed project measurements. The short category response limits generation work, but reading ambiguous narratives still requires inference.

The current service rejects responses that are not an exact allowed category. We have observed formatting/error failures during development, but have not used measured error rates to set these estimates. Keep that validation behavior consistent across models, or explicitly version any baseline changes and use separate runs.

## Model identity

| Tag | Full installed digest | Pin status |
|---|---|---|
| llama3.2:1b | baf6a787fdffd633537aa2eb51cfd54cb93ff08e28040095462bb63daf552878 | Verified using local Ollama model listing |
| llama3.2:3b | Not yet recorded | Pull the chosen tag and record its full local digest before testing |
| qwen2.5:7b | Not yet recorded | Pull the chosen tag and record its full local digest before testing |

The official tag pages currently list the Llama 1B candidate as Q8_0 and the 3B candidate as Q4_K_M. Record the actual quantisation of all locally installed candidates with the final pins. This draft is not a completed pinned candidate manifest until the missing digests are supplied.

## Expected hardest categories

We predict Debt collection and Credit reporting will be the hardest pair to distinguish: narratives often mention both a collector and disputed credit entries. We predict this pair will account for at least 25% of wrong-category predictions, combining both directions and excluding request/output errors.

For the 1B candidate, we predict recall below 65% for both categories. We also expect confusion between Bank account or service and Money transfer or service, because transfers are commonly initiated through a bank account. Mortgage should be easier where the narrative explicitly names mortgage servicing, escrow or foreclosure; we predict at least 75% Mortgage recall for the 1B candidate. These per-category claims assume the final reference set includes examples of each category.

## Comparing predictions with results

Keep these estimates unchanged once the team adopts and commits this record for future runs. Record observed accuracy, median latency, per-category recall and bottleneck evidence separately, then explain departures from the predictions in Slide 11. A later commit cannot establish that this draft predates already completed runs.

## Sources for candidate identity

- [Ollama llama3.2:1b](https://ollama.com/library/llama3.2:1b)
- [Ollama llama3.2:3b](https://ollama.com/library/llama3.2:3b)
- [Ollama qwen2.5:7b](https://ollama.com/library/qwen2.5:7b)

These sources establish candidate availability and model details; they do not substantiate the numerical predictions above.
