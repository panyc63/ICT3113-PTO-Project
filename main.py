"""Synchronous baseline. Tickets enter only through POST /tickets."""
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

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "runtime" / "tickets.db")))
LOG_PATH = Path(os.getenv("LOG_PATH", str(BASE_DIR / "logs" / "service_requests.jsonl")))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2:1b")
MODEL_DIGEST = os.getenv("MODEL_DIGEST", "")
RUN_ID = os.getenv("RUN_ID", "development")
MODEL_TIMEOUT = float(os.getenv("MODEL_TIMEOUT", "120"))

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


@asynccontextmanager
async def lifespan(app):
    init_db()  # Create an empty database; never read or seed from the dataset.
    if RUN_ID != "development" and not MODEL_DIGEST:
        raise RuntimeError("Reported runs require MODEL_DIGEST and a unique RUN_ID")
    if MODEL_DIGEST:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        response.raise_for_status()
        installed = {m["name"]: m["digest"] for m in response.json()["models"]}
        if installed.get(MODEL_NAME) != MODEL_DIGEST:
            raise RuntimeError("Installed model does not match MODEL_NAME and MODEL_DIGEST")
    yield


app = FastAPI(title="Ticket Triage Service", lifespan=lifespan)


@app.middleware("http")
async def audit_request(request: Request, call_next):
    started = time.perf_counter()
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    status = 500
    error = None
    try:
        response = await call_next(request)
        status = response.status_code
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Run-ID"] = RUN_ID
        response.headers["X-Model-Name"] = MODEL_NAME
        response.headers["X-Model-Digest"] = MODEL_DIGEST
        return response
    except Exception as exc:
        error = type(exc).__name__
        raise
    finally:
        logger.info(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": RUN_ID, "request_id": request_id,
            "source_row": request.headers.get("X-Source-Row"),
            "method": request.method, "path": request.url.path,
            "query": request.url.query, "status": status,
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
            "model": MODEL_NAME, "model_digest": MODEL_DIGEST,
            "ticket_id": getattr(request.state, "ticket_id", None),
            "category": getattr(request.state, "category", None),
            "backend": getattr(request.state, "backend", None),
            "model_output": getattr(request.state, "model_output", None),
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


@app.post("/tickets")
def classify_ticket(ticket: TicketRequest, request: Request):
    prompt = f"""You are a financial complaint classifier. Classify the following ticket into EXACTLY one of these categories:
{', '.join(CATEGORIES)}.

Respond with ONLY the exact category name and nothing else.

Ticket Narrative:
{ticket.narrative}"""
    try:
        response = requests.post(f"{OLLAMA_HOST}/api/generate", json={
            "model": MODEL_NAME, "prompt": prompt, "stream": False,
            "options": {"num_gpu": 0},
        }, timeout=MODEL_TIMEOUT)
        response.raise_for_status()
        result = response.json()
        category = result["response"].strip()
        if category not in CATEGORIES:
            request.state.error = "invalid_model_category"
            request.state.model_output = category[:2000]
            raise HTTPException(status_code=502, detail="Ollama returned text that is not an exact allowed category; see model_output in the service log")
        request.state.backend = {key: result.get(key) for key in (
            "total_duration", "load_duration", "prompt_eval_count",
            "prompt_eval_duration", "eval_count", "eval_duration",
        )}
    except requests.Timeout:
        request.state.error = "model_timeout"
        raise HTTPException(status_code=504, detail="Model backend timed out")
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
        rows = conn.execute(
            "SELECT id, narrative, category, created_at FROM tickets WHERE narrative LIKE ?",
            (f"%{q}%",),
        ).fetchall()
    return [dict(zip(("id", "narrative", "category", "created_at"), row)) for row in rows]


@app.get("/stats")
def get_stats():
    with closing(get_db()) as conn:
        counts = dict(conn.execute("SELECT category, COUNT(*) FROM tickets GROUP BY category"))
    return {category: counts.get(category, 0) for category in CATEGORIES}
