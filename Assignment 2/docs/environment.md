# Environment evidence checklist

Fill this record on the original Assignment 1 test machines. Do not guess values. If there was a machine change, document the reason.

| Item | Recorded value |
|---|---|
| Service host OS, CPU model, logical CPU count, RAM | Pending team measurement |
| Docker CPU count and RAM allocation | Pending |
| Ollama container CPU/memory limits | Pending |
| Ollama image digest and version | Pending |
| Model tag/full digest for all three candidates | Compare with `model_config.py` |
| Ollama inference settings, parallelism and context length | Pending verification against A1 |
| Python, service dependencies, Docker/Compose/JMeter/Java versions | Pending |
| Separate load-generator machine specs and network | Pending |
| Warm-up and calibration ticket row numbers | `data/warmup_rows.txt`, `data/calibration_rows.txt` |
| Fixed ordered speed workload | `data/workload_rows.txt` |

Helpful commands on the service host: `docker info`, `docker compose ps`, `docker compose images`, `docker compose exec ollama ollama --version`, `docker compose exec ollama ollama list`, `docker compose exec ollama ollama ps`. Use `docker inspect` to verify the actual original image and container CPU/memory limits. On the generator: `jmeter --version`, `java -version`, `python --version`.

The A2 Compose file preserves A1's CPU-only settings and single inference slot. The same `keep_alive=-1` is used for every A2 model call to retain residency, not to change inference settings. Any A1 resource limits or inference settings imposed outside the checked-in Compose file must be reproduced, recorded and kept constant.
