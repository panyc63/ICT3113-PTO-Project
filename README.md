# ICT3113 Assignment 1 Team P2-11

This repository implements the synchronous ticket triage baseline and prepares test inputs from `data/ict3113_tickets.csv`. Team 11 uses the **1,000 records numbered 11000 through 11999**, inclusive. Row numbers refer to the CSV's `row` column, not physical text lines: many narratives contain line breaks.

The original CSV is preserved. The service does not read it or preload any tickets. The client-side preparation and accuracy tools read it; tickets reach the service one at a time through `POST /tickets`, as required by the assignment.

## Requirement review
| Assignment requirement | Repository status |
| --- | --- |
| Team-only data, rows 11000–11999 | Implemented and validated; 1,000 prepared traffic records |
| Synchronous POST, persistent results, search, seven-category statistics | Implemented; endpoint checks use a mocked model |
| Docker rebuild and Compose setup | Dockerfile and dependencies supplied; Compose configuration validated; live container build/run still needs verification |
| Empty initial service; no direct CSV import | New service container starts empty; existing containers retain posted tickets until recreated |
| CPU-only local Ollama | No GPU device access in Compose; requests set `num_gpu=0`; cloud disabled; capture live `ollama ps` evidence during actual runs |
| Straightforward baseline, no application caching or queues | Preserved; each POST waits for inference and database insertion |
| Every request logged | JSONL audit logs include status, duration, request ID, source row, model tag/digest and run ID, including GET and error responses |
| Protocol, agreement and recorded resolutions | Agreement calculator supplied; team must write/revise protocol, label independently and record adjudications |
| Frozen golden labels and predictions committed before first benchmark | Accuracy runner checks both input files against HEAD; actual final files and freeze commit still missing |
| Quantitative workload and justified numeric requirements | Missing; needs cited ticket/search volumes, peaks, length distribution and measurable targets |
| 3–5 candidate models across at least two size classes, exact tag/digest | Model configuration and digest verification implemented; final candidate selection, pins and justification missing |
| Environment description and separate load-generator machine | Missing; record actual hardware, software, network and scaling limitations |
| Open-loop JMeter load tests; three runs/configuration | Not yet implemented or executed; prepared CSV is ready for a JMeter plan |
| p50/p95/p99, throughput, errors, means/spread, raw JTL and matching logs | Missing; must come from actual runs |
| Accuracy per candidate and category, confusion matrix | Runnable evaluator supplied; final human golden labels and actual measurements pending |
| Stress test determining a system limit | Missing |
| Recommendation defended by measurements and requirements | Missing |
| Maximum 12 slides plus supporting files | Missing; final deck is `Group11.pptx`, due 9 October 2026 at 23:59 Singapore time |

No real model inference or benchmark was run during this review. Mocked automated checks are development verification, not assignment measurement evidence.

## Data preparation and human labelling

The following files have already been prepared in `data/team11/`:

- `team_tickets.csv`: all 1,000 permitted narratives, identified by source row.
- `jmeter_tickets.csv`: the same records as one CSV line per ticket. `payload_b64` is a Base64-encoded UTF-8 JSON request body, preserving embedded newlines, quotes and non-ASCII characters.
- `labels_member1.csv` and `labels_member2.csv`: the same 175 sampled narratives with a blank `category` column. Consumer source labels are deliberately omitted.

### Optional regeneration — skip this for normal setup

The existing `data/team11/` files are ready for labelling. You do **not** need to run preparation again. Only if you deliberately need another copy in a new directory, use:

```powershell
python prepare_data.py --team 11 --output data/team11-new
```

The preparation tool refuses to overwrite an existing directory. Do not replace a frozen sample after viewing model outputs.

The command above creates `data/team11-new/`; it does not update `data/team11/`. The commands below use `data/team11/`. If you choose the new directory as your working copy, change both input paths consistently and keep everyone's work in the chosen directory.

### Manual work — complete before running agreement

The assignment's Step 1 requires: “At least two team members label every ticket independently, following the protocol and without conferring.”

1. Write a shared labelling protocol defining the seven categories and rules for overlapping, ambiguous or apparently out-of-scope complaints.
2. Person A opens `data/team11/labels_member1.csv` in a spreadsheet editor, reads each narrative and fills in the `category` column for all 175 tickets.
3. Person B independently does the same in `data/team11/labels_member2.csv`. Both files contain the **same** tickets, so their answers can be compared. Do not compare answers yet or use model outputs or the consumer source labels to fill the sheets.
4. Save each completed sheet as CSV, keeping the `row` and `narrative` columns unchanged. Keep both independent sheets after adjudication.

Use exactly one of these values in each `category` cell:

- Credit reporting
- Debt collection
- Mortgage
- Credit card
- Bank account or service
- Consumer loan
- Money transfer or service

**Stop here if either sheet still has blank categories.** The sheets were generated blank intentionally; no command automatically completes this human labelling step.

### Run agreement — only after both sheets are complete

```powershell
python calculate_agreement.py data/team11/labels_member1.csv data/team11/labels_member2.csv --output results/agreement
```

This writes Cohen's kappa, raw agreement and a disagreement sheet with blank resolution fields. It rejects mismatched row sets, duplicate IDs, incomplete labels and rows outside Team 11. An undefined kappa is written as `null`, not an invented score.

If you see `ValueError: Missing or invalid category for row 11000 ...`, open the named sheet and check the `category` cell for source row 11000. A blank cell means labelling is still pending; otherwise check that the value exactly matches one of the seven names above. Complete all remaining labels before rerunning. This error is unrelated to Docker or the model backend.

### Discuss disagreements and freeze the final labels

Resolve every disagreement by discussion, record the chosen category and reason, and revise the protocol where needed. Produce `data/team11/golden.csv` with columns `row,category`, covering the same adjudicated sample. Do not use `source_label` as the golden category. Check category coverage before freezing: the evaluator reports `null` for a category with no examples, so such a set cannot substantiate that category's accuracy requirement.

Write the prediction record with the expected bottleneck and reason, expected accuracy and single-request latency for every candidate, and hardest categories with reasons. Commit the finished golden set and predictions **before the first benchmark or model exposure of golden narratives**. Preserve the freeze commit in the report. The tool's HEAD checks do not prove historical timing, independent human labelling or the quality of your predictions; commit history and team records must do that.

## Running the baseline

Start Docker Desktop/the Docker engine first. The review environment had no running Docker engine.

```powershell
docker compose up -d ollama
docker compose exec ollama ollama pull llama3.2:1b
docker compose up -d --build triage-service
```

`llama3.2:1b` preserves the original project's development default; it is not a completed candidate selection. Choose and justify 3–5 local models across at least two parameter-size classes. Pull them ahead of testing. Do not change tags while a run is active.

For each reported run, obtain the full digest from the local Ollama model listing and set it with a unique run ID:

```powershell
$models = (Invoke-RestMethod http://localhost:11434/api/tags).models
$models | Select-Object name,digest,details
$env:MODEL_NAME = 'llama3.2:1b'
$env:MODEL_DIGEST = ($models | Where-Object name -eq $env:MODEL_NAME).digest
$env:RUN_ID = 'llama32-1b-accuracy-01'
docker compose up -d --build --force-recreate triage-service
```

The service refuses to start a reported run without a digest or when the installed tag has a different digest. Development mode can run without a pin. Do not repull/replace a model during a run: the digest is verified at startup, not on every request. Record the Ollama container image digest too; `OLLAMA_IMAGE` can be set to that digest for reproduction, while the default `latest` is only a development convenience.

Each recreated service container starts with an empty SQLite database. Restarting the same container preserves its database. There is no reset API and no bulk import. Keep the container for the entire run. Recreating it discards its tickets, so first retain any database evidence your playbook requires. Logs are retained separately in `logs/<RUN_ID>.jsonl` on the host. Use unique run IDs to prevent mixing runs in the same log.

- `POST /tickets`: body `{"narrative":"..."}`; waits for classification and storage before returning `id` and `category`.
- `GET /search?q=...`: searches stored narratives.
- `GET /stats`: counts every category, including zero counts.

Model HTTP failures and malformed category outputs return 502, timeouts return 504, invalid request bodies return 422. These are logged and must count towards error rates. The service does not silently replace failed predictions with Credit reporting.

The service adds `X-Request-ID`, `X-Run-ID`, `X-Model-Name` and `X-Model-Digest` response headers. Load generators should supply a unique `X-Request-ID` and the source `X-Source-Row`; audit logs record both. The service accepts arbitrary narrative requests as required; team-row restrictions are enforced in dataset preparation and accuracy evaluation, not by trusting caller-supplied headers.

## Accuracy evaluation

Install the dependencies in a local environment using Python 3.12, or use your established Python environment:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
```

After final labels and predictions are committed, run the evaluator from the repository on the separate load-generator machine. Substitute actual model pins, run ID and SUT address:

Saving or staging a file is not enough: it must be present in the latest Git commit (`HEAD`). Once both files are finished, commit them locally; a push is not required for this check. For example, if your prediction record is named `predictions.md`:

```powershell
git add -- data/team11/golden.csv predictions.md
git commit -m "Freeze golden labels and predictions before benchmarking"
```

Use the actual prediction filename if different. A missing prediction record must be written first. If the evaluator says it cannot read `HEAD:data/team11/golden.csv`, the local golden file is not available in the latest commit. Do not commit practice labels as if they were final human labels. After committing, run:

```powershell
python evaluate_accuracy.py data/team11/golden.csv --target-url http://SUT-IP:8000/tickets --prediction-record predictions.md --model EXACT-TAG --digest FULL-DIGEST --run-id UNIQUE-RUN-ID --output results/UNIQUE-RUN-ID
```

The runner joins final labels by `row` to narratives from the original `ict3113_tickets.csv`, verifies service identity, and posts each golden ticket once. It preserves predictions, request IDs, HTTP errors and elapsed times in CSV, with dataset and frozen-input hashes in metadata. `accuracy.json` includes overall accuracy, per-category recall (correct predictions divided by true-category support), and a labelled confusion matrix. Failed requests stay in the denominator and appear in the `ERROR` column. Outputs never overwrite a prior run directory. Do not use this sequential accuracy script for throughput or latency requirement evidence: that requires open-loop JMeter.

## Preparing the JMeter playbook

A complete, exercised `.jmx` playbook and reported runs are still required. Use Apache JMeter's Open Model Thread Group or Precise Throughput Timer; a conventional closed-loop user-count test is not acceptable. The following is the data integration for the future plan, not a completed playbook:

1. Copy `data/team11/jmeter_tickets.csv` to the separate load-generator machine. Configure CSV Data Set Config with UTF-8 encoding, comma delimiter, variable names `row,payload_b64`, ignore first line, recycle on EOF, and sharing across all threads.
2. Add a Groovy JSR223 PreProcessor before the ticket sampler:

   ```groovy
   int sourceRow = Integer.parseInt(vars.get('row'))
   if (sourceRow < 11000 || sourceRow > 11999) {
       throw new IllegalArgumentException('Source row outside Team 11')
   }
   vars.put('payload', new String(java.util.Base64.getDecoder().decode(vars.get('payload_b64')), java.nio.charset.StandardCharsets.UTF_8))
   vars.put('request_id', java.util.UUID.randomUUID().toString())
   ```

3. Send `${payload}` as the raw POST body with `Content-Type: application/json`, `X-Source-Row: ${row}` and `X-Request-ID: ${request_id}`. Do not wrap the decoded payload in quotes or escape it again. Save `row` and `request_id` as JMeter sample variables in the JTL for log reconciliation. Give GET requests their own unique IDs too.
4. Set independent controlled arrival schedules for ticket and search traffic according to the workload model. Keep warm-up and measured periods explicit, and document the database reset policy, search queries and seeded data (if needed, seed only through POST from team rows).
5. Specify exact rates, durations, timeouts, random seeds, assertions, software versions, command lines and stopping criteria before running. Record observed starts and completions to detect generator saturation or growing backlog. Ensure the generator has enough capacity to maintain arrivals under slow responses.
6. Repeat every model/rate configuration three times. Keep raw JTL, matching service JSONL, model pins and environment metadata for each unique run. Calculate p50/p95/p99 response elapsed time, successful ticket throughput, error rate and the mean/spread across the three runs. Explain time windows and treatment of timeouts; do not substitute JMeter's time-to-first-byte `Latency` field for full response time.
7. Execute a preplanned stress test for at least one model, determining a measurable limit. Then compare measurements against the committed predictions and numeric requirements and make the recommendation.

## Automated checks

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
docker compose config --quiet
```

Tests use temporary databases and mocked Ollama responses. They check CSV provenance, all 1,000 narrative payload round-trips, team limits, agreement alignment, error-inclusive accuracy, endpoints, CPU request options, digest mismatch and request logging. They do not establish real model accuracy, CPU performance or Docker runtime behavior.
