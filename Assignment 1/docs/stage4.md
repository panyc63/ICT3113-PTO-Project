# Stage 4: Candidate Models, Requirements and Predictions

**Team:** P2-11  
**Updated:** 9 October 2026  
**Status:** Acceptance benchmarks adopted; model and test-environment validation remain pending.

This report presents three candidate models for the ticket-classification service, the workload they must support, the adopted acceptance benchmarks, and the proposed performance and accuracy forecasts. The evaluation will compare each candidate against these benchmarks to support a model recommendation. Fields marked **Pending** identify decisions or evidence required to complete the evaluation plan.

**Forecast status:** These forecasts are provisional planning estimates and must not be presented as the predictions used for actual benchmark runs. A pre-test comparison requires evidence that the prediction baseline and golden set were committed before the first benchmark. Once frozen, the prediction baseline must remain unchanged.

## 1. Objectives and readiness

| Deliverable | Current status | Next action |
| --- | --- | --- |
| Candidate models | Three candidates, their full digests and selection rationale are recorded. | Confirm installed versions and quantisation details. |
| Performance and accuracy requirements | Acceptance benchmarks and their justification are adopted for the rounded peak workload of 160 ticket submissions/hour and 320 searches/hour. | Measure each candidate against the adopted benchmarks; confirm whether dashboard traffic is included. |
| Predictions | Bottleneck, accuracy, latency and difficult-category forecasts are defined. | Strengthen the numerical rationale and establish the dated baseline for comparison with results. |

## 2. Proposed candidate models

The proposed evaluation covers three models across the 1B, 3B and 7B size classes, meeting the required candidate-count and size-class coverage. The selection allows the client to assess the trade-off between classification accuracy and CPU processing time. References: S1 and S6.

| Ollama model tag | Size class | Selection rationale |
| --- | ---: | --- |
| `llama3.2:1b` | 1B | Smallest candidate; expected to provide the fastest CPU inference. It is also the service's current development default. |
| `llama3.2:3b` | 3B | Provides a comparison with the 1B model within the Llama family. |
| `qwen2.5:7b` | 7B | Adds a larger size class and a different model family. |

Model family and quantisation also vary across the candidates. Performance differences therefore cannot be attributed solely to parameter count.

### Model versions

All three model digests are recorded below. Each digest identifies the model version intended for evaluation. Before testing, the installed versions will be checked against these digests to support reproducible results.

| Model tag | Full model digest | Status |
| --- | --- | --- |
| `llama3.2:1b` | `baf6a787fdffd633537aa2eb51cfd54cb93ff08e28040095462bb63daf552878` | Recorded |
| `llama3.2:3b` | `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72` | Recorded |
| `qwen2.5:7b` | `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` | Recorded |

The recorded quantisation references are `Q8_0` for Llama 1B and `Q4_K_M` for Llama 3B. **Pending:** confirm the actual installed quantisation for all three candidates and document Qwen's quantisation.

## 3. Client workload

The workload assessment provides the demand estimates used to set acceptance targets. Ticket intake and search demand are defined separately, then combined for performance testing. Operating assumptions remain pending confirmation; service capacity will be measured during testing. Reference: S2.

### Ticket intake

The planning baseline is **81,813 complaints per six months**, equivalent to **629.33 tickets per working day**, using **130 working days and eight active hours per day**. The daily profile allocates 50% of intake to two peak hours and the remaining 50% to six non-peak hours. Reference: S2, Sections 2–3.

| Period | Ticket submissions/hour |
| --- | ---: |
| Non-peak | 52.44 |
| Whole active-day average | 78.67 |
| Peak | 157.33 |

### Search demand

The baseline assumes **two searches per incoming ticket**, giving **163,626 searches per six months** and **1,258.66 searches per working day**. Search demand follows the same daily activity profile. These figures describe search requests only. Reference: S2, Section 4.

| Period | Search requests/hour |
| --- | ---: |
| Non-peak | 104.89 |
| Whole active-day average | 157.33 |
| Peak | 314.67 |

The two-search assumption remains pending confirmation. One-search and four-search scenarios assess sensitivity to lookup activity using the same daily activity profile.

### Combined evaluation workload

The performance evaluation brings the ticket and search streams together using the **1:2 submission-to-search mix**. Reference: S2, Section 6.

| Period | Ticket submissions/hour | Search requests/hour | Combined requests/hour |
| --- | ---: | ---: | ---: |
| Non-peak | 52.44 | 104.89 | 157.33 |
| Whole active-day average | 78.67 | 157.33 | 236.00 |
| Peak | 157.33 | 314.67 | 472.00 |

The adopted rounded peak test rates are **160 ticket submissions/hour and 320 searches/hour**, approximately **1.7% above the derived peak**. Optional shared-dashboard monitoring would add **60 `GET /stats` requests/hour**, or **480 requests per working day**. **Pending:** confirm whether dashboard traffic is included in the final workload.

### Ticket-length profile

The evaluation uses Team 11's **1,000 complaint narratives, rows 11000–11999**, sampled uniformly or replayed as a shuffled complete pass to represent the measured length profile. Reference: S2, Section 5.

| Narrative length | Share of traffic under uniform sampling |
| --- | ---: |
| 1–500 characters | 23.8% |
| 501–1,000 characters | 37.6% |
| 1,001–1,500 characters | 24.6% |
| 1,501–2,000 characters | 14.0% |
| More than 2,000 characters | 0.0% |

The request narratives have a mean length of **897.86 characters**, a median of **804.5 characters**, and a p95 length of **1,818 characters**. This profile represents the supplied test pool; its representativeness for the client's customer population has not been established. The measurement method and input checksum are documented in S2, Section 7.

## 4. Acceptance requirements

The following benchmarks define the required service quality. Latency, throughput and endpoint failure rates apply under sustained, independent open-loop arrivals of **160 `POST /tickets` submissions/hour and 320 `GET /search` requests/hour**. Accuracy is assessed separately on all **175 golden-set tickets** for each candidate, with one outstanding request at a time. References: S2 and S6.

| Measure | Testable target | Reason |
| --- | --- | --- |
| POST latency | `POST /tickets` p95 ≤ 15 seconds. | Complete most tickets before the 22.5-second mean arrival gap at the rounded peak test rate of 160 tickets/hour. |
| Search latency | `GET /search` p95 ≤ 1 second. | Keep case lookup responsive during intake. |
| Throughput / errors | Mean ≥ 158.4 successful `POST /tickets` completions/hour; ≤ 1% failures per endpoint. | Serve 99% of 160 offered tickets/hour, above the estimated peak demand of 157.33 tickets/hour. |
| Overall accuracy | ≥ 80%, equivalent to at least 140 correct classifications out of 175. | Limit misrouting to 20% in staff-assisted triage. |
| Each category recall | ≥ 70% for all seven categories. | Prevent strong categories masking poor routing elsewhere. |

The fixed categories are **Credit reporting, Debt collection, Mortgage, Credit card, Bank account or service, Consumer loan, and Money transfer or service**.

Successful POST throughput counts requests that complete with a valid category and a stored ticket. Classification correctness is assessed separately against the golden labels. Calculate throughput for each measured run as successful completions divided by the measurement duration in hours, then report the mean and spread across the three runs required per configuration.

Calculate endpoint failure rates as failed requests divided by attempted requests × 100, separately for `POST /tickets` and `GET /search`. Timeouts, unsuccessful HTTP responses and invalid API results count as failures. Report latency percentiles, throughput and failure rates for the same measurement window in each run. Dashboard inclusion remains a separate workload decision.

Acceptance requirements define the service quality the client needs. Forecasts estimate what each candidate may achieve. The adopted benchmarks will be applied consistently to every candidate, with any unmet requirement reported explicitly.

## 5. Evaluation conditions and measures

### Baseline conditions

| Item | Evaluation condition |
| --- | --- |
| Inference | Local CPU-only Ollama; model requests set `num_gpu=0`. |
| Service behaviour | Synchronous classification, with no application cache or application queue. |
| Ollama parallel inference slots | One, configured with `OLLAMA_NUM_PARALLEL=1`. |
| Single-request latency forecast | One outstanding request at a time, after the model has loaded, with the same prompt and output format across candidates. |
| Cold starts | Separate from the warmed-up single-request latency forecasts. |
| Accuracy sample | The forecasts assume 175 final reference-labelled tickets. |
| Load generator | A separate machine is required for reported performance testing. |
| Performance workload | Independent open-loop ticket and search arrival streams at the adopted rates. |
| Model timeout | The current default is 120 seconds. The adopted `POST /tickets` response-time benchmark is p95 ≤ 15 seconds. |

The baseline uses local CPU inference and consistent service settings across all candidates. **Pending:** document the CPU, memory and full test environment needed to interpret latency results. References: S1, S3 and S4; workload method: S2, Section 7.

### Accuracy

Classification quality will be evaluated using:

```text
Overall accuracy (%) = correctly classified golden-set tickets / total golden-set tickets × 100
Per-category accuracy/recall (%) = correctly classified tickets of that category / total golden-set tickets of that category × 100
```

Failed requests and invalid outputs count as incorrect and are included in an `ERROR` column in the confusion matrix. A category with no golden-set examples has an undefined per-category score. Reference: S5.

The forecast percentages are judgement-based estimates of future scores. Measured accuracy will be calculated from the correctly classified golden-set tickets using these formulas.

### Latency

The latency forecasts cover the **median full `POST /tickets` response time with one outstanding request and a loaded model**. Peak-load p95 and p99 response times require separate measurement. Reference: S1.

## 6. Performance and accuracy forecasts

### Expected bottleneck

We expect **CPU inference in Ollama** to be the primary bottleneck. Processing a narrative and generating a category should take more time than inserting a SQLite row or serialising the HTTP response.

The evaluation will test the following hypotheses:

- For successful warmed-up single requests, Ollama's reported total duration will account for **more than 80%** of the service request duration.
- Arrivals above processing capacity will produce more outstanding requests, increasing p95 response times and eventually timeouts.
- Larger candidates will reach this limit at lower arrival rates.

Service logs and model timings will be used to assess these hypotheses. Reference: S1.

### Accuracy and single-request latency

| Model tag | Forecast overall accuracy | Forecast median latency |
| --- | ---: | ---: |
| `llama3.2:1b` | 65% | 3 seconds |
| `llama3.2:3b` | 75% | 7 seconds |
| `qwen2.5:7b` | 80% | 15 seconds |

The forecast rationale is:

- The 1B candidate is expected to be fastest, but more prone to confusing a product mentioned in the narrative with the main complaint.
- The 3B candidate is expected to improve accuracy by **10 percentage points**, with more than twice the median latency.
- The 7B candidate is expected to improve accuracy by a further **5 percentage points**, with roughly twice the 3B latency.
- The short category response limits output-generation work, while interpreting ambiguous narratives still requires inference.

**Forecast confidence:** the rationale supports the expected ordering of the candidates, but the exact percentages and response times do not yet have a quantitative derivation. They are provisional estimates that require further justification and validation. Formatting and request failures observed during development have not been used to calibrate these values. Reference: S1.

### Expected difficult categories

| Category or comparison | Rationale | Forecast |
| --- | --- | --- |
| Debt collection versus Credit reporting | A narrative may mention both a collector and disputed credit entries. | This pair will account for **at least 25% of wrong-category predictions**, combining both directions and excluding request/output errors. For the 1B candidate, recall will be **below 65% for each category**. |
| Bank account or service versus Money transfer or service | Transfers are commonly initiated through a bank account, creating overlapping cues. | No numerical forecast recorded. |
| Mortgage | Explicit references to mortgage servicing, escrow or foreclosure are expected to make the category easier to identify. | For the 1B candidate, Mortgage recall will be **at least 75%**. |

These category forecasts are conditional on the final golden set containing examples of the relevant categories. The adopted acceptance benchmark requires recall of at least 70% for each of the seven categories. Reference: S1.

## 7. Actions to complete the evaluation plan

| Action | Status |
| --- | --- |
| Record the full digest for each of the three candidates. | Complete |
| Confirm the candidate selection and its justification. | Pending |
| Verify installed model versions and document quantisation. | Pending |
| Document test hardware and operating conditions. | Pending |
| Confirm the working calendar, active hours and daily peak profile. | Pending |
| Confirm the baseline of two searches per ticket. | Pending |
| Adopt the combined evaluation workload and decide whether to include dashboard traffic. | 160 submissions/hour and 320 searches/hour adopted; dashboard inclusion pending. |
| Agree the response-time target, percentile, endpoint and load condition. | Complete: POST p95 ≤ 15 seconds and search p95 ≤ 1 second under the adopted peak workload. |
| Agree the throughput target in successful classifications/hour. | Complete: mean ≥ 158.4 successful POST completions/hour and ≤ 1% failures per endpoint. |
| Agree overall and per-category accuracy targets based on misrouting consequences. | Complete: overall accuracy ≥ 80% and recall ≥ 70% for each category. |
| Strengthen the numerical forecast rationale and state its uncertainty. | Pending |
| Establish the dated, frozen prediction and golden-set versions supporting any pre-test comparison. | Pending |

## 8. References

| Reference | Document or implementation | Purpose |
| --- | --- | --- |
| S1 | [predictions.md](</D:/Files/Proton Drive/My files/[3] SIT/[7] Year 3 - Tri 1/[3] ICT3113 - Performance Testing and Optimisation/[4] Assignments/[1] A1/Code/predictions.md>) | Initial candidate selection, Llama 1B digest, forecast values, evaluation conditions and forecast-baseline qualification. |
| S2 | [stage3.md](</D:/Files/Proton Drive/My files/[3] SIT/[7] Year 3 - Tri 1/[3] ICT3113 - Performance Testing and Optimisation/[4] Assignments/[1] A1/Code/docs/stage3.md>) | Ticket intake and arrival profile (Sections 2–3), search demand (Section 4), ticket-length profile (Section 5), combined evaluation workload (Section 6), and measurement and load-generator methods (Section 7). |
| S3 | [docker-compose.yml](</D:/Files/Proton Drive/My files/[3] SIT/[7] Year 3 - Tri 1/[3] ICT3113 - Performance Testing and Optimisation/[4] Assignments/[1] A1/Code/docker-compose.yml>) | Model default, timeout, local Ollama configuration and parallelism. |
| S4 | [main.py](</D:/Files/Proton Drive/My files/[3] SIT/[7] Year 3 - Tri 1/[3] ICT3113 - Performance Testing and Optimisation/[4] Assignments/[1] A1/Code/main.py>) | Synchronous service, CPU request setting and default timeout. |
| S5 | [evaluate_accuracy.py](</D:/Files/Proton Drive/My files/[3] SIT/[7] Year 3 - Tri 1/[3] ICT3113 - Performance Testing and Optimisation/[4] Assignments/[1] A1/Code/evaluate_accuracy.py>) | Overall accuracy, per-category accuracy/recall and error treatment. |
| S6 | [Assignment 1 Worksheet.docx](</D:/Files/Proton Drive/My files/[3] SIT/[7] Year 3 - Tri 1/[3] ICT3113 - Performance Testing and Optimisation/[4] Assignments/[1] A1/Assignment 1 Worksheet.docx>) | Stage 4 deliverables, fixed categories and benchmark-freeze requirements. |
