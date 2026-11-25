# Assignment 1 — Project Delivery Plan

This plan defines the **six official delivery stages**, their required outputs and completion criteria. The project will establish reference labels, implement a baseline service, assess client demand, evaluate candidate models and present an evidence-based recommendation. Delivery requirements follow the [assignment worksheet](</D:/Files/Proton Drive/My files/[3] SIT/[7] Year 3 - Tri 1/[3] ICT3113 - Performance Testing and Optimisation/[4] Assignments/[1] A1/Assignment 1 Worksheet.docx>).

**Team:** P2-11  
**Updated:** 9 October 2026  
**Data scope:** numbered rows **11000–11999**, inclusive, for all labelling and test traffic.  
**Submission deadline:** **9 October 2026, 23:59**, via xSiTe.

## Stage 1 — Reference labels

The reference dataset will provide the basis for assessing classification quality.

| Planned activity | Required output |
| --- | --- |
| Establish definitions for the seven fixed categories and rules for ambiguous, overlapping and out-of-scope tickets. | Written labelling protocol. |
| Select **150–200 tickets** from the allocated Team 11 rows. | Sample identified by source row number. |
| Obtain independent labels from **at least two team members for every selected ticket**, without conferring. | Separate completed label sheets. |
| Assess inter-annotator agreement. | Agreement statistic. |
| Resolve every disagreement, record the reasons and revise the protocol where required. | Resolution record and revised protocol. |
| Freeze and commit the final labels before any model receives the selected narratives. | Final golden set and Git commit evidence. |

**Completion criteria:** independent labelling, agreement assessment and adjudication are complete, and the final golden set is frozen and committed.

## Stage 2 — Baseline service

The baseline will support ticket classification, retrieval and category reporting using local CPU inference.

| Planned activity | Required output |
| --- | --- |
| Provide `POST /tickets` to accept one narrative, classify it, store it and return its category. | Working classification endpoint. |
| Provide `GET /search` and `GET /stats`. | Working retrieval and category-count endpoints. |
| Configure local CPU-only inference through Ollama. | Reproducible Docker Compose setup. |
| Use synchronous classification with sequential calls and no application caching or queues. | Straightforward baseline implementation. |
| Initialise the service empty and submit tickets individually through the API. | Correct intake behaviour. |
| Record every request. | Service logs supporting the reported measurements. |

**Completion criteria:** an independent reviewer can rebuild and run the service, exercise all three endpoints and inspect the request logs.

## Stage 3 — Client workload assessment

The workload assessment establishes the demand the service must support. The report follows this structure:

| Work area | Report section | Required output |
| --- | ---: | --- |
| Service scope and planning basis | 1 | Published complaint-volume evidence, service scope and explicit operating assumptions. |
| Estimated ticket intake | 2 | Ticket-volume calculations over the planning period, per working day and per active hour. |
| Daily arrival profile | 3 | Peak and non-peak ticket arrival rates. |
| Search request demand | 4 | Search totals and search-only hourly rates, with search-frequency sensitivity scenarios. |
| Ticket-length profile | 5 | Measured length ranges, proportions and summary statistics for the permitted traffic pool. |
| Evaluation workload and pending decisions | 6 | Combined ticket and search traffic, adopted test rates and the optional dashboard workload. |
| Technical appendix | 7 | Measurement method, input checksum, reproducible script and load-generator configuration. |

**Current readiness:** the assessment is drafted. Working hours, the daily peak profile, search frequency and dashboard inclusion remain pending confirmation.

**Completion criteria:** ticket volume, search activity, peak and non-peak demand, and ticket-length distribution have a defensible basis, with traceable sources and explicit assumptions. The combined evaluation workload is defined.

**Workload report:** [stage3.md](</D:/Files/Proton Drive/My files/[3] SIT/[7] Year 3 - Tri 1/[3] ICT3113 - Performance Testing and Optimisation/[4] Assignments/[1] A1/Code/docs/stage3.md>).

## Stage 4 — Model selection, acceptance requirements and forecasts

This stage defines the candidate models, the service quality required by the client and the results expected before evaluation.

| Deliverable | Required content |
| --- | --- |
| **Candidate models** | **3–5 models** spanning **at least two parameter-size classes**, with exact Ollama **tags and digests** and a selection rationale. |
| **Acceptance requirements** | At least one response-time target, one throughput target, and classification-accuracy targets **overall and per category**. Targets specify numeric thresholds, relevant percentiles and load conditions, with justification against client needs and estimated peak demand. |
| **Forecasts** | Expected bottleneck and rationale; expected accuracy and single-request latency for **each candidate on the test hardware**; difficult categories and rationale. Forecasts are specific and testable. |

**Current readiness:** three candidates and their digests are recorded. Acceptance benchmarks are adopted for **160 ticket submissions/hour and 320 searches/hour**: **POST p95 ≤ 15 seconds**, **search p95 ≤ 1 second**, **mean ≥ 158.4 successful POST completions/hour**, **≤ 1% failures per endpoint**, **overall accuracy ≥ 80% (at least 140/175)**, and **recall ≥ 70% for each category**. Installed versions, quantisation, test hardware and the numerical forecast rationale require further work. Dashboard inclusion and the dated prediction baseline for comparison with benchmark results remain to be established.

**Completion criteria:** model choices and acceptance requirements are justified, and the prediction record is frozen and committed **before the first benchmark**. Predictions cannot be revised after benchmarking.

**Model and evaluation proposal:** [stage4.md](</D:/Files/Proton Drive/My files/[3] SIT/[7] Year 3 - Tri 1/[3] ICT3113 - Performance Testing and Optimisation/[4] Assignments/[1] A1/Code/docs/stage4.md>).

## Stage 5 — Testing and evidence

The evaluation will document CPU, memory, operating system, software, network, machine roles, limitations and the implications for scaling to the client.

**The load generator will run on a separate physical machine from the system under test.**

| Test | Evaluation method | Required evidence |
| --- | --- | --- |
| **Load testing** | JMeter with controlled **open-loop arrivals**, using the Open Model Thread Group or Precise Throughput Timer. **Three repetitions per configuration**, covering the candidates and tested arrival rates. | p50, p95 and p99 latency; achieved throughput; error rate; means and spread across runs. |
| **Accuracy testing** | **Every golden-set ticket** submitted through `POST /tickets` for **each candidate**. | Overall accuracy, per-category accuracy and a confusion matrix. |
| **Stress testing** | A test establishing a meaningful system limit for **at least one candidate**. | The limit found, supporting measurements and an explanation of failure or saturation behaviour. |

Each test will have a reproducible playbook. Raw **`.jtl` files and service logs** will be retained in Git, with reported measurements traceable to those records.

**Completion criteria:** required testing is complete, results are traceable, and unmet requirements and bottlenecks are diagnosed. Implementing remedies is not required for Assignment 1.

## Stage 6 — Recommendation and submission

The final recommendation will assess measured performance against the client's acceptance requirements and explain the trade-offs.

| Planned activity | Required output |
| --- | --- |
| Assess measured results against the acceptance requirements. | Evidence showing which candidates meet or miss each target. |
| Compare forecasts with actual results. | Identification of correct and incorrect forecasts, with explanations for differences. |
| Recommend a candidate and explain the trade-offs. | A recommendation supported by the project's measurements. |
| Identify requirements that no candidate meets. | Clearly stated limitations. |
| Prepare the presentation and supporting files. | Complete submission package. |

**Completion criteria:** the recommendation follows from the requirements and measurements. An evidence-based finding that **no candidate meets every requirement** is an acceptable outcome.

## Delivery sequence and dependencies

- **Stages 1–3 can proceed in parallel.**
- Stage 4 uses the workload assessment, golden-set definitions, baseline implementation and test hardware to establish requirements and forecasts.
- **Stage 5 begins only after Stages 1–4 are complete**, with the golden set and prediction record already frozen and committed.
- Stage 6 uses the measurements from Stage 5 to support the recommendation.

## Presentation structure

| Slide | Content |
| ---: | --- |
| 1 | Cover: group, members, student IDs, title and repository link |
| 2 | Service architecture and endpoints |
| 3 | Workload assessment: ticket intake, search demand and combined evaluation traffic |
| 4 | Performance and accuracy requirements |
| 5 | Candidate models and exact pins |
| 6 | Golden-set construction and agreement |
| 7 | Test environment |
| 8 | Test playbooks |
| 9 | Load and stress results |
| 10 | Accuracy results |
| 11 | Predictions versus outcomes, recommendation and defence |
| 12 | References and acknowledgements, including model licences |

## Submission package

The package will be submitted via xSiTe by **9 October 2026, 23:59**:

| Deliverable | Required content |
| --- | --- |
| **Group11.pptx** | Presentation of no more than 12 slides. |
| Final golden set | Reference labels and source row numbers. |
| Prediction record | Frozen forecasts supporting the comparison with measured results. |
| Labelling protocol | Category rules and all revisions. |
| Independent label sheets and agreement statistic | Evidence of independent labelling and inter-annotator agreement. |

## Repository evidence

| Evidence | Purpose |
| --- | --- |
| Runnable source and Docker setup | Reproduce the service. |
| Golden set and prediction record, committed before the first benchmark | Establish the reference labels and pre-test forecast baseline. |
| Freeze commit history | Verify the timing and preserved versions of the golden set and prediction record. |
| Raw JMeter `.jtl` results and service logs | Reconcile reported measurements with the underlying test evidence. |
