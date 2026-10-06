# Stage 3: Client Workload Assessment

**Team:** P2-11  
**Research and measurement date:** 5 October 2026  
**Updated:** 6 October 2026  
**Status:** Proposed workload; operating assumptions are pending confirmation.

This report estimates demand for a central complaints intake and retrieval service. The planning scenario represents a large financial services organisation, using published complaint volumes, explicit operating assumptions and measured test-data characteristics.

Estimated intake is approximately **630 tickets per working day**, with a peak of **157.33 new tickets/hour and 314.67 searches/hour**. Proposed peak test rates are **160 ticket submissions/hour and 320 searches/hour**. These rates establish the demand to assess; response-time, throughput and accuracy acceptance targets remain pending.

## 1. Service scope and planning basis

The service will classify incoming complaints and allow staff to retrieve stored cases. Each new complaint produces one ticket submission through `POST /tickets`; staff searches use `GET /search`. Complaint resolution and subsequent customer handling sit outside this workload assessment.

The workload is based on three evidence types:

| Input | Evidence type | Planning basis |
| --- | --- | --- |
| Six-month complaint volume | Published figure used as a proxy | HSBC UK Bank plc's January–June 2026 disclosure |
| Working hours, searches and busy periods | Operating assumptions | Estimated working patterns and service usage; public disclosures do not provide hourly intake or search counts |
| Ticket-length distribution | Measured test-data profile | All 1,000 Team 11 complaint narratives used by the load generator |

The FCA describes complaints **opened** as complaints received by firms. We therefore use opened counts to estimate arrivals. [FCA, firm-specific complaints data](https://www.fca.org.uk/data/complaints-data/firm-level).

### Complaint-volume benchmark

HSBC UK Bank plc reports the following opened complaints for **1 January–30 June 2026**, covering HSBC UK Bank, first direct and Marks & Spencer Financial Services. [HSBC UK, complaints data](https://www.hsbc.co.uk/help/feedback-and-complaints/complaints-data/).

| Published product group | Complaints opened |
| --- | ---: |
| Banking & Credit Cards | 73,367 |
| Home Finance | 4,246 |
| Credit Related | 4,200 |
| **Selected total, calculated** | **81,813** |

The selected product groups cover banking, cards, mortgages and credit activities relevant to the service. Insurance, pensions and investments are excluded. These published groups differ from the service's seven classification categories. Their complaint counts establish the intake baseline; their proportions are not used to set the classification-category mix.

We adopt **81,813 complaints per six months** as the planning baseline for the client scenario. This assumes that the full selected volume enters the service and that each opened complaint produces one initial ticket. Repeat contacts and retries would add demand beyond this baseline.

For comparison, Metro Bank reports 8,716 banking/card, 134 home-finance and 3,225 credit-related opened complaints in the same period: **12,075 in total**, calculated. This illustrates the lower intake a smaller institution may experience. The assessment consistently uses the HSBC-scale planning baseline. [Metro Bank, complaints data](https://www.metrobankonline.co.uk/help-and-support/forms/give-us-feedback/complaints-data/).

## 2. Estimated ticket intake

### Planning assumptions

1. **One initial ticket per complaint.** The baseline covers initial intake; follow-up submissions, duplicate contacts and retries would increase demand.
2. **130 intake working days per six months.** This uses a planning approximation of 260 working days per year, rather than the source period's exact weekday and holiday calendar.
3. **Eight active intake hours per working day, from 09:00 to 17:00 in the client's local time.** The six-month volume is distributed across these working periods. Overnight and weekend intake are outside the modelled profile.
4. **An unchanged volume in the second half of the year for annualisation.** The resulting annual total is a planning equivalent; seasonal changes have not been estimated.

### Calculations

```text
Six-month tickets = 73,367 + 4,246 + 4,200 = 81,813
Annualised tickets = 81,813 × 2 = 163,626
Tickets per working day = 81,813 / 130 = 629.33
Average tickets per active hour = 629.33 / 8 = 78.67
Average POST arrival rate = 78.67 requests/hour
```

The baseline corresponds to approximately **630 tickets per working day**, or **79 per active hour**, with an average spacing of **45.8 seconds between new tickets**. These figures describe incoming demand. Actual service throughput will be measured separately.

## 3. Daily arrival profile

The proposed daily profile places **50% of intake in two peak hours: 09:00–10:00 and 13:00–14:00**. This represents increased activity at the start of the morning and afternoon work periods. The profile is a planning assumption because the published complaint data does not establish hourly arrival patterns.

The remaining six hours receive the other 50%. Peak intake is therefore twice the average hourly intake, while the daily total remains unchanged:

```text
Peak rate = (629.330769 × 50%) / 2 hours = 157.332692 tickets/hour
Non-peak rate = (629.330769 × 50%) / 6 hours = 52.444231 tickets/hour
```

| Period | Hours per day | Tickets/hour | Average spacing |
| --- | ---: | ---: | ---: |
| Non-peak: 10:00–13:00 and 14:00–17:00 | 6 | 52.44 | 68.6 seconds |
| Peak: 09:00–10:00 and 13:00–14:00 | 2 | 157.33 | 22.9 seconds |
| Whole active-day average | 8 | 78.67 | 45.8 seconds |

The rates and spacings describe hourly averages; individual arrivals will vary. Exceptional events, month-end effects and annual seasonality remain outside the planning baseline because the available evidence does not quantify them.

## 4. Search request demand

The baseline assumes **two searches per incoming ticket**: one to find related complaints during initial review and one to locate or check the case during follow-up. This is an operating assumption about service usage, independent of staff headcount. It assumes that case work keeps pace with intake over the reporting period and follows the same broad daily profile.

Search demand is calculated from the six-month search total. The daily profile allocates 50% of searches to two peak hours and the remaining 50% to six non-peak hours, using the operating pattern defined in Section 3.

```text
Six-month searches = 81,813 × 2 = 163,626
Searches per working day = 163,626 / 130 = 1,258.66
Average search rate = 1,258.661538 / 8 = 157.33 searches/hour
Peak search rate = (1,258.661538 × 50%) / 2 = 314.67 searches/hour
Non-peak search rate = (1,258.661538 × 50%) / 6 = 104.89 searches/hour
```

| Period | Search requests/hour |
| --- | ---: |
| Non-peak | 104.89 |
| Whole active-day average | 157.33 |
| Peak | 314.67 |

### Search-frequency sensitivity

Search frequency affects search demand. The following scenarios vary the number of searches per ticket while retaining the same daily activity profile. The figures show search requests during peak hours:

| Searches per ticket | Peak search requests/hour |
| --- | ---: |
| 1: lighter lookup activity | 157.33 |
| **2: adopted base assumption** | **314.67** |
| 4: heavier lookup activity | 629.33 |

The two-search scenario remains the planning baseline. The alternatives indicate sensitivity to staff usage patterns and can inform additional testing; they do not establish measured search rates or acceptance targets.

## 5. Ticket-length profile

The test-data profile is measured from **all 1,000 Team 11 complaint narratives, rows 11000–11999 inclusive**, supplied from the US CFPB database. It provides a consistent input mix for comparing model performance.

Mean narrative length is **897.86 characters**, the median is **804.5 characters**, and at least 95% of narratives contain **1,818 characters or fewer**. The measurement method and input checksum are retained in the technical appendix.

| Statistic | Narrative characters | Whitespace-separated words |
| --- | ---: | ---: |
| Minimum | 200 | 29 |
| Mean | 897.86 | 159.47 |
| Median | 804.5 | 145 |
| p90 | 1,658 | 284 |
| p95 | 1,818 | 317 |
| p99 | 1,947 | 356 |
| Maximum | 1,995 | 377 |

| Narrative length | Tickets | Expected share of uniformly sampled traffic |
| --- | ---: | ---: |
| 1–500 characters | 238 | 23.8% |
| 501–1,000 characters | 376 | 37.6% |
| 1,001–1,500 characters | 246 | 24.6% |
| 1,501–2,000 characters | 140 | 14.0% |
| More than 2,000 characters | 0 | 0.0% |
| **Total** | **1,000** | **100.0%** |

The evaluation will use uniform sampling from the full pool or a shuffled complete pass to represent this distribution. A short partial pass through sorted records may produce a different length mix.

The figures cover narrative text. The classification prompt adds to the model input, while request formatting adds transport overhead. Character and word counts are not token counts; tokenisation can differ between models.

The measured profile represents the **supplied test pool**. Its representativeness for the client's customer population has not been established. The CFPB also cautions that its public database is not a statistical sample of all consumer experiences. [CFPB, Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/).

## 6. Evaluation workload and pending decisions

The evaluation combines the ticket-submission rates from Section 3 with the search rates from Section 4:

| Period | Ticket submissions/hour | Search requests/hour | Combined requests/hour |
| --- | ---: | ---: | ---: |
| Non-peak | 52.44 | 104.89 | 157.33 |
| Whole active-day average | 78.67 | 157.33 | 236.00 |
| Peak | 157.33 | 314.67 | 472.00 |

The submission-to-search request mix is **1:2**. Testing will include both request types to assess how shared service resources affect classification and retrieval.

The proposed evaluation uses **157.33 new tickets/hour plus 314.67 searches/hour** as the estimated peak demand, with the measured narrative-length mix. Rounded test rates of **160 ticket submissions/hour and 320 searches/hour** provide a convenient test workload approximately **1.7% above the derived peak**.

Optional monitoring assumes **one shared dashboard refreshing statistics once per minute during the eight-hour day** through `GET /stats`. This adds **60 requests/hour**, or **480/day**, and would increase estimated peak demand to approximately **532 total requests/hour**. **Pending:** confirm whether dashboard traffic is included in the evaluation workload.

Non-peak and average-day rates will provide lower-load comparisons. Higher arrival rates will be used to investigate capacity and overload separately from expected client demand. For context, **3,600 tickets/hour** is approximately **22.9 times** the estimated peak intake.

The evaluation will hold the intended arrival rate independently of processing speed. This allows the client to assess whether the service can sustain demand as classification times increase.

| Decision | Status |
| --- | --- |
| Confirm working hours and the proposed daily peak profile. | Pending |
| Confirm the baseline of two searches per ticket. | Pending |
| Include or exclude shared-dashboard traffic. | Pending |
| Agree response-time targets and their measurement percentiles. | Pending in Stage 4 |
| Agree successful-classification throughput and accuracy targets. | Pending in Stage 4 |

Acceptance targets will be justified against the adopted workload and the consequences of slow or incorrect classification. Model results will then be compared against those targets. The complaint-volume baseline remains demand-led.

## 7. Technical appendix

### Measurement method

The measurement decodes each `payload_b64` value in [jmeter_tickets.csv](</D:/Files/Proton Drive/My files/[3] SIT/[7] Year 3 - Tri 1/[3] ICT3113 - Performance Testing and Optimisation/[4] Assignments/[1] A1/Code/data/team11/jmeter_tickets.csv>), parses the JSON and measures the `narrative` string used in the request. All row IDs were checked, and every narrative matches [team_tickets.csv](</D:/Files/Proton Drive/My files/[3] SIT/[7] Year 3 - Tri 1/[3] ICT3113 - Performance Testing and Optimisation/[4] Assignments/[1] A1/Code/data/team11/team_tickets.csv>) after line-ending normalisation.

Characters are Unicode characters counted with Python `len(narrative)`. Words are whitespace-separated items counted with `len(narrative.split())`. Percentiles use the nearest-rank definition: sorted item at `ceil(p × 1,000)`, using one-based indexing. The median is the mean of the two middle values.

The request narratives use LF line endings. The prepared CSV preserves CRLF inside some narratives. Counting those characters literally produces a mean of **899.88 characters**, a p95 of **1,823** and a maximum of **2,005**. This formatting difference accounts for the variation between direct CSV counts and the request-payload measurements used in this report.

### Reproducible measurement

The following read-only script runs from the [Code directory](</D:/Files/Proton Drive/My files/[3] SIT/[7] Year 3 - Tri 1/[3] ICT3113 - Performance Testing and Optimisation/[4] Assignments/[1] A1/Code>). It produces aggregate statistics and the input checksum without displaying complaint narratives or invoking a model.

```python
import base64
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

path = Path("data/team11/jmeter_tickets.csv")
with path.open(encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))
assert len(rows) == 1000
assert sorted(int(row["row"]) for row in rows) == list(range(11000, 12000))
narratives = [
    json.loads(base64.b64decode(row["payload_b64"]))["narrative"]
    for row in rows
]

for name, values in (
    ("characters", [len(text) for text in narratives]),
    ("words", [len(text.split()) for text in narratives]),
):
    values.sort()
    print(name, "min", values[0], "mean", statistics.mean(values),
          "median", statistics.median(values), "max", values[-1])
    for p in (0.90, 0.95, 0.99):
        print(f"p{int(p * 100)}", values[math.ceil(p * len(values)) - 1])

lengths = [len(text) for text in narratives]
for low, high in ((1, 500), (501, 1000), (1001, 1500),
                  (1501, 2000), (2001, float("inf"))):
    count = sum(low <= length <= high for length in lengths)
    print(low, high, count, f"{count / len(lengths):.1%}")
print("input SHA-256", hashlib.sha256(path.read_bytes()).hexdigest())
```

Measured input SHA-256:

```text
9956f9f809817fc42c4fe10db8c5e58c80980295e37b5b5cbba9498abd5435dc
```

### Load-generator configuration

Performance testing will use open-loop arrivals. The search stream will operate independently of ticket-submission completion and will query cases already submitted through the API. The service starts empty and receives tickets individually through `POST /tickets`.

Where the load generator requires requests/second, divide the hourly rate by **3,600**. Thus, **160 submissions/hour = 0.044444 requests/second** and **320 searches/hour = 0.088889 requests/second**. Hourly rates remain the reporting convention.

### Evidence and version control

The research and measurement date records when the supporting analysis was completed. This updated report establishes a planning scenario; it does not establish a historical pre-benchmark freeze. Any claim that the workload was fixed before testing requires the corresponding dated project version.

## References

All web sources accessed on **5 October 2026**. The source periods are stated separately from the access date.

1. [HSBC UK — Complaints data](https://www.hsbc.co.uk/help/feedback-and-complaints/complaints-data/). HSBC UK Bank plc, 1 January–30 June 2026. Primary source for the adopted complaint-volume proxy.
2. [Metro Bank — Complaints data](https://www.metrobankonline.co.uk/help-and-support/forms/give-us-feedback/complaints-data/). 1 January–30 June 2026. Comparison for a smaller firm's intake volume.
3. [FCA — Firm-specific complaints data](https://www.fca.org.uk/data/complaints-data/firm-level). Defines opened/received and closed measures. Its displayed aggregate reporting period is 2025 H2; the volume figures above come directly from the firms' 2026 H1 disclosures.
4. [CFPB — Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/). Context for the course extract and its representativeness limits.
5. [Assignment 1 Worksheet.docx](</D:/Files/Proton Drive/My files/[3] SIT/[7] Year 3 - Tri 1/[3] ICT3113 - Performance Testing and Optimisation/[4] Assignments/[1] A1/Assignment 1 Worksheet.docx>). Step 3 workload requirements, dataset scope and Team 11 row allocation.
6. [jmeter_tickets.csv](</D:/Files/Proton Drive/My files/[3] SIT/[7] Year 3 - Tri 1/[3] ICT3113 - Performance Testing and Optimisation/[4] Assignments/[1] A1/Code/data/team11/jmeter_tickets.csv>). Measurement source for all 1,000 request narratives; method and checksum in the technical appendix.
