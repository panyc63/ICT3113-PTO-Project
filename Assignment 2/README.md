# ICT3113 Assignment 2 — Group P2-11

This directory implements the Assignment 2 cascade without modifying Assignment 1. It is a preparation/measurement toolkit, not a completed benchmark report. There are no fabricated accuracy or speed results. All formal measurements must run on the unchanged Assignment 1 service host, with a separate JMeter generator. The team owns the escalation choices, predictions, experiments and recommendation.

## 0. Set up the models

From `Assignment 2` on the service host, run

```powershell
python .\0_setup\setup_ollama.py
```

[Step 0 — Model setup](0_setup/README.md) explains how the script selects the Ollama image, prepares the model volume, and verifies the three Assignment 1 models.

## 1. Define the accuracy limits

Step 1 uses the archived A1 Qwen predictions on the frozen even rows. Qwen scored 63/90 (70.00%), giving an overall floor of 54/90 (60.00%). The report gives the seven category floors, source files, reproduction command and reuse conditions. [Step 1 report](1_accuracy-limits/step1-report.md)

From the repository root (PowerShell):

```powershell
git add -- 'Assignment 2/data/golden_tuning.csv' 'Assignment 2/data/golden_test.csv'
git commit -m 'Freeze Assignment 2 golden tuning and test split'
```

The two generated CSVs retain the 175 original labels. Odd **source row IDs** (the A1 `row` column, not physical CSV lines) form the tuning set (85); even source IDs form the test set (90). Both are sorted. If your lecturer explicitly intended sorted-list ordinal parity instead, resolve this interpretation before measuring.

The workload is already prepared: 3 distinct typical-length warm-up tickets, 3 distinct calibration tickets, and 819 ordered non-golden speed tickets. Long tickets are interleaved in the fixed workload. No ticket overlaps any other set. The JMeter thread group uses a fixed random seed and a shared non-recycling CSV. Validate the actual sent row sequence across runs. Python checks the actual dataset contents.

Git commits are required by the assignment for evidence, not by the Python programs. If the split is already committed, this step is done. Use your Git client (including VS Code Source Control or GitHub Desktop) to commit the split, final predictions/rule and ordered workload as required by the brief. No Git installation or PATH configuration is needed to run the scripts.

## 2. Design the cascade

### Check model residency before cascade tuning

Complete [model setup](0_setup/README.md) and verify the original hardware allocation in [the environment record](docs/environment.md) before running this check.

**Check memory before choosing a pair.** Start a clean Ollama container, check the original A1 settings, then run:

```powershell
New-Item -ItemType Directory -Force results | Out-Null
docker compose restart ollama
python benchmark.py warmup --model llama3.2:3b --model qwen2.5:7b --output results/memory-3b-7b.json
```

This interleaves three fixed warm-up tickets for each model using the unchanged prompt, records `ollama ps` and `/api/ps` evidence, and checks both models remain resident on CPU. It never changes memory allocation. A failed attempt should be saved; try `llama3.2:1b` + `qwen2.5:7b`, then `llama3.2:1b` + `llama3.2:3b` if necessary. If no pair fits, the brief allows reporting that evidence and testing singles instead.

### Tune the chosen pair on the odd rows

Recover A1 per-ticket prediction CSVs for both models and verify unchanged digest, prompt, version, machine. The checked-in A1 1B CSV may be a development run; verify its provenance before reuse. If a record is unavailable or conditions changed, start each model on the original host and run a new tuning evaluation on the load generator, e.g.:

```powershell
python start_config.py --model llama3.2:3b --run-id tuning-3b
python accuracy.py run --split tuning --model llama3.2:3b --run-id tuning-3b --output results/tuning-3b
python start_config.py --model qwen2.5:7b --run-id tuning-7b
python accuracy.py run --split tuning --model qwen2.5:7b --run-id tuning-7b --output results/tuning-7b
```

These commands use localhost for tuning on the SUT. From a different computer, add `--url` followed by the actual service machine's HTTP URL; `SUT-IP` in older examples is not a literal hostname. The formal JMeter load generator must run on a separate machine. The Python launcher replaces `start_config.ps1` and waits until the correct model/run ID is ready on port 8000.

Once tuning predictions for both selected models are available:

```powershell
python accuracy.py tune --small results/tuning-3b/predictions.csv --large results/tuning-7b/predictions.csv --output results/tuning-analysis.json
```

The analysis shows accuracy, confusion matrices, and **precision by each predicted category**. Optionally estimate a proposed category list with repeatable `--accept 'Credit reporting|Debt collection'` arguments (illustrative syntax only, NOT selected settings). The estimate uses only tuning rows; it is not a measured cascade. The team selects two settings, documents the category lists, false-acceptance evidence, rationale and resident pair in `escalation_rule.md`, and completes `predictions.md` before formal testing.

## 3. Record predictions

Record the expected fastest qualifying configuration, the escalation fraction, accuracy and median latency for each cascade setting, and the categories expected to lose accuracy. The worksheet requires the predictions and rule to be committed before the first A2 benchmark. [Prediction record](predictions.md) · [Escalation rule](escalation_rule.md)

```powershell
git add -- predictions.md escalation_rule.md
git commit -m 'Freeze escalation rule and Assignment 2 predictions before held-out testing'
```

## 4. Test and measure

- **4-1. Top model alone.** Run `python 4-1_top-model-benchmark/run_step4_1.py` to measure Qwen on the 90 test tickets. [Instructions](4-1_top-model-benchmark/README.md) · [Results](4-1_top-model-benchmark/step4-1-report.md)
- **4-2. Other A1 models alone.** Run `python 4-2_other-models-benchmark/run_step4_2.py` to measure Llama 1B and 3B individually against the Step 1 limits. [Instructions](4-2_other-models-benchmark/README.md) · [Results](4-2_other-models-benchmark/step4-2-report.md)

### Held-out accuracy

For each single model and both chosen cascade settings, use a unique run ID. On SUT:

```powershell
python start_config.py --model qwen2.5:7b --run-id acc-qwen
```

On generator:

```powershell
python accuracy.py run --split test --model qwen2.5:7b --url http://SUT-IP:8000 --run-id acc-qwen --output results/acc-qwen
python accuracy.py score --split test --predictions results/acc-qwen/predictions.csv --output results/acc-qwen/accuracy.json
```

For a single model with verified unchanged A1 predictions, use `accuracy.py reuse --split test --model MODEL --predictions PATH --confirm-unchanged --output RESULTS_DIR`; then score. Reuse is not allowed for A1 speed data.

For a cascade, start it with the selected pair and list, for example syntax:

```powershell
python start_config.py --model llama3.2:3b --large-model qwen2.5:7b --setting 1 --accept-categories '<team-selected pipe-separated categories>' --run-id acc-cascade1
docker compose restart ollama
python benchmark.py warmup --model llama3.2:3b --model qwen2.5:7b --output results/acc-cascade1-warmup.json
```

Run the actual accuracy evaluation with `--mode cascade --model llama3.2:3b --run-id acc-cascade1`. Copy the SUT's `logs/acc-cascade1.jsonl` to the generator, then score with `--cascade-logs logs/acc-cascade1.jsonl`. Repeat using setting 2 and its fixed acceptance list. Raw data include errors in the accuracy denominator.

To compare the saved A2 results to the Step 1 limits, run the following from `Assignment 2` with an unused output filename.

```powershell
python accuracy.py compare --top 1_accuracy-limits/a2-test-rows/accuracy.json --config 'Qwen=4-1_top-model-benchmark/results/qwen-20261127T113825Z-3a6842ff/accuracy.json' --config 'Llama1B=4-2_other-models-benchmark/results/step2-20261127T125523Z-624d7491/llama-1b/accuracy.json' --config 'Llama3B=4-2_other-models-benchmark/results/step2-20261127T125523Z-624d7491/llama-3b/accuracy.json' --config 'Cascade1=results/acc-cascade1/accuracy.json' --config 'Cascade2=results/acc-cascade2/accuracy.json' --output results/comparison-step1.json
```

This derives the overall floor from Qwen's test accuracy minus 10 percentage points, each category floor minus 15 points, and qualifies configurations using both. Small category supports must be disclosed (Credit card has seven test tickets).

### Calibrate and speed-test (three runs per configuration)

On SUT, start the top single model with a calibration run ID; restart Ollama and warm up using `benchmark.py warmup --model qwen2.5:7b --output results/calibration-warmup.json`. Separate generator:

```powershell
python benchmark.py calibrate --model qwen2.5:7b --url http://SUT-IP:8000 --run-id calibration --output results/calibration.json
```

Record the three times and rows, S, fixed rate, duration, timeout and drain. Set the same model-call timeout for all configurations, sufficient for the longest individual call; HTTP sampler timeout comes from calibration. The generator uses only POST traffic. Every configuration that passes both floors, plus BOTH cascade settings irrespective of accuracy, gets three runs. The top model always gets three runs. Do not reuse any A1 speed figure.

For **each** run, start a new unique service run ID, restart Ollama and run `benchmark.py warmup` with the matching model(s), copy the fresh warmup evidence to generator, then:

```powershell
python benchmark.py run --model qwen2.5:7b --run-id speed-qwen-1 --url http://SUT-IP:8000 --jmeter 'C:/path/to/jmeter.bat' --calibration results/calibration.json --warmup-evidence results/speed-qwen-1-warmup.json --output results/speed-qwen-1
```

This records `/stats` before/after, requests started (separate `starts.csv`), raw `.jtl`, JMeter logs, parameters, and warm-up evidence. Copy matching SUT `logs/<run-id>.jsonl` to the generator. Verify `ollama ps` after each cascade run as well. Reconcile missing/unfinished requests rather than dropping runs. Make sure the ordered row sequence matches across runs and the count is sufficient; first run the plan in the JMeter GUI to verify the saved plan loads, without running a benchmark prematurely.

Example three-run summary:

```powershell
python benchmark.py summary --run results/speed-qwen-1 logs/speed-qwen-1.jsonl --run results/speed-qwen-2 logs/speed-qwen-2.jsonl --run results/speed-qwen-3 logs/speed-qwen-3.jsonl --output results/speed-qwen-summary.json
```

Report p50 per run, mean, range, standard deviation, pooled p95 with sample count, completed throughput (per configured arrival-window second), JMeter error/unfinished counts, and escalation fraction with its log denominator. Check stats/log reconciliation. Do not report p99. Compare speed arrival rate to A1's 157.33 tickets/hour estimated peak (rounded to 160 for A1). A lower rate does not validate client peak capacity.

## 5. Recommendation

Recommend the fastest configuration that passes the Step 1 overall and per-category limits. Compare its measured latency and accuracy with Qwen alone.

## Submission

Use the eight required slides in the A2 brief: cover, cascade, environment/method, accuracy, speed, trade-off chart, predictions/recommendation, limitations/references/licences/AI declaration. Use the fastest qualifying configuration, even a single model. Link every figure to raw data. State the team designed/chose the final rule, ran tests and made the recommendation; AI assisted with the code/test tooling. Submit `Group11_A2.pptx`, finalized prediction record, escalation rule and `data/workload_rows.txt`; keep all raw results/logs in Git. Deadline 27 November 23:59 Singapore time.
