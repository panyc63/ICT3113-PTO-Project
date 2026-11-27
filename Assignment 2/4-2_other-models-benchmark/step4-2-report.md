# Step 4-2 — Test each other A1 model alone

**Pending.** The current experiment still needs held-out test results for Llama 3.2 1B and Llama 3.2 3B. Their Step 1 tuning scores describe the 85 odd rows. To determine standalone qualification, classify all 90 even rows with each model and compare each result with the overall and seven category floors from Qwen’s Step 1 test run.

From `Assignment 2`, run `python 4-2_other-models-benchmark/run_step4_2.py`. Each model’s predictions, confusion matrix and logs, along with the batch comparison, will be saved in this step. [Runner instructions](README.md) · [Step 1 accuracy limits](../1_accuracy-limits/step1-report.md)
