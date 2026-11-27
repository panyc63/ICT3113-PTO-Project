# Step 4-1 — Test the top model alone

Qwen’s standalone accuracy measurement for this experiment is the Step 1 run on the 90 even-row test tickets. Qwen scored **64 right and 26 wrong (71.11%)**. This sets the overall floor at **55/90 (61.11%)**. The Step 1 report lists all seven category floors and links to the original logs. [Step 1 Qwen results](../1_accuracy-limits/step1-report.md) · [Held-out scores and confusion matrix](../1_accuracy-limits/results/step1-20261127T140752Z-14aa0cd1/test/qwen-7b/accuracy.json)

Qwen’s speed benchmark requires separate calibrated JMeter runs on the non-golden workload. [Speed-test procedure](../README.md#calibrate-and-speed-test-three-runs-per-configuration)
