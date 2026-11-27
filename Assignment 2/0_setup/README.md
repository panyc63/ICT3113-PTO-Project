# Step 0 — Model setup

On the Assignment 1 service host, start Docker Desktop and activate a Python environment with the [A2 requirements](../requirements.txt) installed. From this folder, run

```powershell
python setup_ollama.py
```

The script prepares `llama3.2:1b`, `llama3.2:3b`, and `qwen2.5:7b`. It looks for the original Ollama image and model volume, including volumes created under an older Compose project name. If the image is missing, it downloads the image tag from A1's Compose file. If the cache is incomplete, it downloads missing models into a dedicated A2 volume. It may stop the original course service containers to release their ports.

Setup checks all three installed model digests against the [A1 model pins](../model_config.py). It writes its image and volume choices to `Assignment 2/.env`, its launcher state to `Assignment 2/.ollama-reuse.json`, and evidence of the image, Ollama version, digests, and cache recovery to `Assignment 2/results/ollama-setup-*.json`. If the original Ollama version cannot be verified, record that limitation and rerun single-model accuracy before using the results.

The [Ollama Compose configuration](ollama.compose.yml) defines the CPU-only service and persistent model volume. The [A2 Compose file](../docker-compose.yml) includes it for every benchmark step. To inspect the resolved configuration from this folder, run `docker compose config`.
