"""FastAPI application setup, model pin verification and request audit logging."""
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
import logging
import time
from typing import Any
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import Response
import requests

from api import runtime
from api.routes.create_ticket import router as create_ticket_router
from api.routes.search_tickets import router as search_tickets_router
from api.routes.get_stats import router as get_stats_router

runtime.LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logger: logging.Logger = logging.getLogger("triage.audit")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    handler: logging.FileHandler = logging.FileHandler(runtime.LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    runtime.init_db()  # Create an empty database; never read or seed from the dataset.
    if runtime.RUN_ID != "development" and not runtime.MODEL_DIGEST:
        raise RuntimeError("Reported runs require MODEL_DIGEST and a unique RUN_ID")
    if runtime.MODEL_DIGEST:
        response: requests.Response = requests.get(f"{runtime.OLLAMA_HOST}/api/tags", timeout=10)
        response.raise_for_status()
        installed: dict[str, str] = {m["name"]: m["digest"] for m in response.json()["models"]}
        if installed.get(runtime.MODEL_NAME) != runtime.MODEL_DIGEST:
            raise RuntimeError("Installed model does not match MODEL_NAME and MODEL_DIGEST")
    yield


app: FastAPI = FastAPI(title="Ticket Triage Service", lifespan=lifespan)


@app.middleware("http")
async def audit_request(
    request: Request, call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    started: float = time.perf_counter()
    request_id: str = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    status: int = 500
    error: str | None = None
    try:
        response: Response = await call_next(request)
        status = response.status_code
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Run-ID"] = runtime.RUN_ID
        response.headers["X-Model-Name"] = runtime.MODEL_NAME
        response.headers["X-Model-Digest"] = runtime.MODEL_DIGEST
        response.headers["X-Output-Format"] = runtime.OUTPUT_FORMAT
        return response
    except Exception as exc:
        error = type(exc).__name__
        raise
    finally:
        record: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": runtime.RUN_ID, "request_id": request_id,
            "source_row": request.headers.get("X-Source-Row"),
            "method": request.method, "path": request.url.path,
            "query": request.url.query, "status": status,
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
            "model": runtime.MODEL_NAME, "model_digest": runtime.MODEL_DIGEST,
            "output_format": runtime.OUTPUT_FORMAT,
            "ticket_id": getattr(request.state, "ticket_id", None),
            "category": getattr(request.state, "category", None),
            "backend": getattr(request.state, "backend", None),
            "model_output": getattr(request.state, "model_output", None),
            "error": error or getattr(request.state, "error", None),
        }
        logger.info(json.dumps(record))


app.include_router(create_ticket_router)
app.include_router(search_tickets_router)
app.include_router(get_stats_router)
