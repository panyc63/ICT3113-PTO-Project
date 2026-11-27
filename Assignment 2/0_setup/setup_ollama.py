"""Reuse the Assignment 1 Ollama cache, or restore the recorded models if deleted."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model_config import MODEL_DIGESTS, verify_installed_models

A1 = ROOT.parent / "Assignment 1"
ENV_FILE = ROOT / ".env"
STATE_FILE = ROOT / ".ollama-reuse.json"


def docker(*args):
    result = subprocess.run(["docker", *args], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"Docker failed: {args}")
    return result.stdout.strip()


def docker_progress(*args):
    """Stream potentially long downloads rather than hiding their progress."""
    result = subprocess.run(["docker", *args], cwd=ROOT, check=False)
    if result.returncode:
        raise RuntimeError(f"Docker command failed (exit {result.returncode}): {' '.join(args)}")


def inspect(kind, item):
    return json.loads(docker(kind, "inspect", item))[0]


def compose_config(folder):
    return json.loads(docker("compose", "--project-directory", str(folder), "-f",
                             str(folder / "docker-compose.yml"), "config", "--format", "json"))


def original_container_models(container):
    for mount in container.get("Mounts", []):
        if mount.get("Destination") == "/root/.ollama" and mount.get("Type") == "volume":
            return mount.get("Name")
    return None


def probe_volume(volume, image_id):
    # The Ollama digest is the SHA-256 of its model manifest. Read only these
    # three manifests from the existing volume; no model is loaded/downloaded.
    script = "for p in llama3.2/1b llama3.2/3b qwen2.5/7b; do f=/mnt/ollama/models/manifests/registry.ollama.ai/library/$p; if [ -f \"$f\" ]; then sha256sum \"$f\"; fi; done"
    output = docker("run", "--rm", "--pull", "never", "--network", "none", "--read-only",
                    "--mount", f"type=volume,source={volume},target=/mnt/ollama,readonly",
                    "--entrypoint", "/bin/sh", image_id, "-c", script)
    found = {}
    for line in output.splitlines():
        digest, _, path = line.partition(" ")
        if "/library/" not in path:
            continue
        family, tag = path.strip().rsplit("/", 2)[-2:]
        found[f"{family}:{tag}"] = digest
    return found


def save_config(image, volume):
    # Preserve any unrelated .env settings. Use fresh internal variable names
    # so stale OLLAMA_IMAGE/OLLAMA_VOLUME_NAME from earlier shell commands cannot override them.
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines() if ENV_FILE.exists() else []
    keys = {"A2_OLLAMA_IMAGE": image, "A2_OLLAMA_VOLUME_NAME": volume}
    lines = [line for line in lines if line.partition("=")[0].strip() not in keys]
    lines.extend(f"{key}={value}" for key, value in keys.items())
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def is_a1_container(container, project):
    labels = container.get("Config", {}).get("Labels") or {}
    directory = labels.get("com.docker.compose.project.working_dir", "").lower()
    return (labels.get("com.docker.compose.project") == project or
            any(token in directory for token in ("ict3113", "performance testing", "[1] a1", "assignment 1")))


def main():
    a1 = compose_config(A1)
    a2_project = compose_config(ROOT)["name"]
    default_volume = a1["volumes"]["ollama_storage"]["name"]
    a1_project = a1["name"]
    print(f"Assignment 1 Compose volume: {default_volume}", flush=True)
    names = docker("volume", "ls", "--format", "{{.Name}}").splitlines()
    candidates = [name for name in names if name == "ollama_storage" or name.endswith("_ollama_storage")]
    tagged = docker("volume", "ls", "--filter", "label=com.docker.compose.volume=ollama_storage", "--format", "{{.Name}}").splitlines()
    candidates = list(dict.fromkeys(candidates + tagged))
    container_ids = docker("ps", "-a", "--filter", "label=com.docker.compose.service=ollama", "--format", "{{.ID}}").splitlines()
    containers = [inspect("container", cid) for cid in container_ids]
    old = [c for c in containers if c.get("Config", {}).get("Labels", {}).get("com.docker.compose.project") != a2_project
           and is_a1_container(c, a1_project)]
    original = next((c for c in old if c["Config"]["Labels"].get("com.docker.compose.project") == a1_project), None)
    fallback = original or next(iter(old), None)
    configured_image = a1["services"]["ollama"]["image"]
    image_origin = "original_container" if fallback else "locally_available_a1_image"
    if fallback:
        local_image = inspect("image", fallback["Image"])
    else:
        try:
            local_image = inspect("image", configured_image)
        except RuntimeError:
            # The original Compose file used the latest tag; if the old image
            # was deleted its historical version cannot be inferred from that tag.
            print(f"Original local Ollama image unavailable. Downloading {configured_image}...", flush=True)
            docker_progress("pull", configured_image)
            local_image = inspect("image", configured_image)
            image_origin = "downloaded_a1_configured_image"
    image_id = local_image["Id"]
    # Prefer the actual A1 container mount, then the A1 directory's Compose name,
    # then legacy volumes (e.g. when the project used to be in a folder named Code).
    candidates.sort(key=lambda v: (v != (original_container_models(original) if original else default_volume),
                                   v != default_volume, v.startswith(a2_project + "_"), v))
    selected = None
    for volume in candidates:
        print(f"Checking {volume} for the three Assignment 1 model digests...", flush=True)
        found = probe_volume(volume, image_id)
        missing = [model for model, digest in MODEL_DIGESTS.items() if found.get(model) != digest]
        if not missing:
            selected = volume
            break
        print(f"  Missing or different: {', '.join(missing)}")
    restoring = selected is None
    if restoring:
        # Never overwrite or delete an old A1 volume. Restore into a dedicated
        # A2 volume, reusing any correctly downloaded models on subsequent retries.
        selected = f"{a2_project}_restored_ollama_storage"
        print(f"No complete original model cache found. Restoring into {selected}.", flush=True)
        docker("volume", "create", selected)
    source = next((c for c in old if original_container_models(c) == selected), None)
    if source:
        local_image = inspect("image", source["Image"])
        image_origin = "original_container"
    repo_digests = local_image.get("RepoDigests") or []
    image = next((digest for digest in repo_digests if "ollama/ollama@" in digest), local_image["Id"])
    project_container = source or fallback
    project = project_container["Config"]["Labels"].get("com.docker.compose.project") if project_container else None
    print(f"Using volume {selected} and Ollama image {image}", flush=True)
    if image_origin != "original_container":
        print("The original Ollama image version could not be confirmed. Record the current version and remeasure accuracy rather than assuming A1 results are reusable.", flush=True)
    save_config(image, selected)
    if project and project != a2_project:
        # Stop only the known original project's running triage/Ollama containers
        # to release their ports; never remove a container or volume.
        for service in ("triage-service", "ollama"):
            running = docker("ps", "--filter", f"label=com.docker.compose.project={project}", "--filter",
                             f"label=com.docker.compose.service={service}", "--format", "{{.ID}}").splitlines()
            for cid in running:
                print(f"Stopping Assignment 1 {service} to release its port (container/data retained).", flush=True)
                docker("stop", cid)
    # Ignore stale shell settings for the new internal variables as well.
    os.environ["A2_OLLAMA_IMAGE"] = image
    os.environ["A2_OLLAMA_VOLUME_NAME"] = selected
    print(docker("compose", "up", "-d", "--wait", "--wait-timeout", "120", "--force-recreate", "--pull", "never", "ollama"))
    def installed_models():
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=10)
        response.raise_for_status()
        return {model["name"]: model["digest"] for model in response.json()["models"]}

    if restoring:
        installed = installed_models()
        for model, digest in MODEL_DIGESTS.items():
            if installed.get(model) != digest:
                print(f"Downloading {model} to the restored A2 cache...", flush=True)
                docker_progress("compose", "exec", "-T", "ollama", "ollama", "pull", model)
    actual_models = installed_models()
    version = docker("compose", "exec", "-T", "ollama", "ollama", "--version")
    evidence = {"timestamp": datetime.now(timezone.utc).isoformat(), "image": image,
                "image_origin": image_origin, "ollama_version": version, "volume": selected,
                "restored_model_cache": restoring or selected.endswith("_restored_ollama_storage"),
                "source_project": project, "expected_model_digests": MODEL_DIGESTS,
                "installed_model_digests": actual_models,
                "all_model_digests_match": all(actual_models.get(model) == digest for model, digest in MODEL_DIGESTS.items())}
    results = ROOT / "results"
    results.mkdir(exist_ok=True)
    evidence_path = results / ("ollama-setup-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"Saved setup evidence: {evidence_path.relative_to(ROOT)}", flush=True)
    verify_installed_models(actual_models, MODEL_DIGESTS)
    STATE_FILE.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(docker("compose", "exec", "-T", "ollama", "ollama", "list"))
    print("Ollama setup complete. All three Assignment 1 model digests match.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, FileNotFoundError, requests.RequestException) as exc:
        sys.exit(f"Setup failed: {exc}")
