"""Synchronous Assignment 1-compatible triage service with optional cascade."""
from contextlib import asynccontextmanager, closing
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import sqlite3
import time
import uuid

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator
import requests

from categories import CATEGORIES
from model_config import (MODEL_DIGESTS, OUTPUT_FORMAT, accept_categories, generate_payload,
                          parse_category, should_escalate)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "runtime/tickets.db")))
LOG_PATH = Path(os.getenv("LOG_PATH", str(BASE_DIR / "logs/service_requests.jsonl")))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
MODE = os.getenv("MODE", "single")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2:1b")
MODEL_DIGEST = os.getenv("MODEL_DIGEST", "")
LARGE_MODEL = os.getenv("LARGE_MODEL", "")
LARGE_MODEL_DIGEST = os.getenv("LARGE_MODEL_DIGEST", "")
CASCADE_SETTING = os.getenv("CASCADE_SETTING", "")
ACCEPTED = accept_categories(os.getenv("ACCEPT_CATEGORIES", ""))
RUN_ID = os.getenv("RUN_ID", "development")
MODEL_TIMEOUT = float(os.getenv("MODEL_TIMEOUT", "600"))

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger("triage.audit")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


def get_db():
    return sqlite3.connect(DB_PATH)


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(get_db()) as conn, conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            narrative TEXT NOT NULL,
            category TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")


def verify_configuration():
    if MODE not in {"single", "cascade"}:
        raise RuntimeError("MODE must be single or cascade")
    if MODEL_TIMEOUT <= 0:
        raise RuntimeError("MODEL_TIMEOUT must be positive")
    models = {MODEL_NAME: MODEL_DIGEST}
    if MODE == "cascade":
        if MODEL_NAME == LARGE_MODEL or not LARGE_MODEL or CASCADE_SETTING not in {"1", "2"}:
            raise RuntimeError("Cascade requires two distinct models and CASCADE_SETTING 1 or 2")
        models[LARGE_MODEL] = LARGE_MODEL_DIGEST
    if not set(models) <= set(MODEL_DIGESTS):
        raise RuntimeError("Only Assignment 1 candidate tags are allowed")
    if RUN_ID != "development" or any(models.values()):
        for model, digest in models.items():
            if digest != MODEL_DIGESTS[model]:
                raise RuntimeError(f"Missing/wrong Assignment 1 digest for {model}")
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        response.raise_for_status()
        installed = {m["name"]: m["digest"] for m in response.json()["models"]}
        for model, digest in models.items():
            if installed.get(model) != digest:
                raise RuntimeError(f"Installed model does not match Assignment 1 digest: {model}")


@asynccontextmanager
async def lifespan(app):
    verify_configuration()
    init_db()
    yield


app = FastAPI(title="Ticket Triage Service", lifespan=lifespan)


@app.middleware("http")
async def audit_request(request: Request, call_next):
    started = time.perf_counter()
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    status, error = 500, None
    try:
        response = await call_next(request)
        status = response.status_code
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Run-ID"] = RUN_ID
        response.headers["X-Model-Name"] = MODEL_NAME
        response.headers["X-Model-Digest"] = MODEL_DIGEST
        response.headers["X-Output-Format"] = OUTPUT_FORMAT
        return response
    except Exception as exc:
        error = type(exc).__name__
        raise
    finally:
        logger.info(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(), "run_id": RUN_ID,
            "request_id": request_id, "source_row": request.headers.get("X-Source-Row"),
            "method": request.method, "path": request.url.path, "query": request.url.query,
            "status": status, "duration_ms": round((time.perf_counter() - started) * 1000, 3),
            "mode": MODE, "model": MODEL_NAME, "model_digest": MODEL_DIGEST,
            "large_model": LARGE_MODEL if MODE == "cascade" else None,
            "large_model_digest": LARGE_MODEL_DIGEST if MODE == "cascade" else None,
            "cascade_setting": CASCADE_SETTING if MODE == "cascade" else None,
            "accept_categories": sorted(ACCEPTED) if MODE == "cascade" else None,
            "output_format": OUTPUT_FORMAT,
            "ticket_id": getattr(request.state, "ticket_id", None),
            "category": getattr(request.state, "category", None),
            "small_model_prediction": getattr(request.state, "small_model_prediction", None),
            "escalated": getattr(request.state, "escalated", None),
            "escalation_reason": getattr(request.state, "escalation_reason", None),
            "final_model": getattr(request.state, "final_model", None),
            "model_calls": getattr(request.state, "model_calls", []),
            "error": error or getattr(request.state, "error", None),
        }))


class TicketRequest(BaseModel):
    narrative: str = Field(min_length=1)

    @field_validator("narrative")
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError("narrative must contain text")
        return value


class InvalidCategory(ValueError):
    pass


def classify_model(model, narrative, request):
    info = {"model": model, "digest": MODEL_DIGESTS[model]}
    request.state.model_calls.append(info)
    start = time.perf_counter()
    try:
        response = requests.post(f"{OLLAMA_HOST}/api/generate",
                                 json=generate_payload(model, narrative), timeout=MODEL_TIMEOUT)
        response.raise_for_status()
        result = response.json()
        info["backend"] = {key: result.get(key) for key in (
            "total_duration", "load_duration", "prompt_eval_count", "prompt_eval_duration",
            "eval_count", "eval_duration")}
        raw = result["response"]
        info["model_output"] = raw[:2000] if isinstance(raw, str) else repr(raw)[:2000]
        try:
            category = parse_category(raw)
        except (ValueError, TypeError) as exc:
            raise InvalidCategory("invalid_model_category") from exc
        info["category"] = category
        return category
    except (requests.RequestException, ValueError, KeyError, TypeError, AttributeError) as exc:
        info["error"] = type(exc).__name__
        raise
    finally:
        info["duration_ms"] = round((time.perf_counter() - start) * 1000, 3)


@app.post("/tickets")
def classify_ticket(ticket: TicketRequest, request: Request):
    request.state.model_calls = []
    request.state.escalated = False if MODE == "cascade" else None
    try:
        try:
            category = classify_model(MODEL_NAME, ticket.narrative, request)
        except InvalidCategory:
            if MODE != "cascade":
                raise
            category = "ERROR"
        final_model = MODEL_NAME
        if MODE == "cascade":
            request.state.small_model_prediction = category
            if should_escalate(category, ACCEPTED):
                request.state.escalated = True
                request.state.escalation_reason = "invalid_small_output" if category == "ERROR" else "category_not_accepted"
                final_model = LARGE_MODEL
                category = classify_model(LARGE_MODEL, ticket.narrative, request)
        request.state.final_model = final_model
    except requests.Timeout:
        request.state.error = "model_timeout"
        raise HTTPException(status_code=504, detail="Model backend timed out")
    except InvalidCategory:
        request.state.error = "invalid_model_category"
        raise HTTPException(status_code=502, detail="Ollama returned invalid category JSON; see model_output in the service log")
    except (requests.RequestException, ValueError, KeyError, TypeError, AttributeError) as exc:
        request.state.error = type(exc).__name__
        raise HTTPException(status_code=502, detail="Model backend returned an error or invalid category")
    with closing(get_db()) as conn, conn:
        cursor = conn.execute("INSERT INTO tickets (narrative, category) VALUES (?, ?)",
                              (ticket.narrative, category))
        ticket_id = cursor.lastrowid
    request.state.ticket_id = ticket_id
    request.state.category = category
    return {"id": ticket_id, "category": category}


@app.get("/search")
def search_tickets(q: str = Query(..., min_length=1)):
    with closing(get_db()) as conn:
        rows = conn.execute("SELECT id, narrative, category, created_at FROM tickets WHERE narrative LIKE ?",
                            (f"%{q}%",)).fetchall()
    return [dict(zip(("id", "narrative", "category", "created_at"), row)) for row in rows]


@app.get("/stats")
def get_stats():
    with closing(get_db()) as conn:
        counts = dict(conn.execute("SELECT category, COUNT(*) FROM tickets GROUP BY category").fetchall())
    return {category: counts.get(category, 0) for category in CATEGORIES}
