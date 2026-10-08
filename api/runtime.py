"""Shared runtime configuration and SQLite setup for the FastAPI routes."""
from contextlib import closing
import os
from pathlib import Path
import sqlite3

BASE_DIR: Path = Path(__file__).resolve().parent.parent
DB_PATH: Path = Path(os.getenv("DB_PATH", str(BASE_DIR / "runtime" / "tickets.db")))
LOG_PATH: Path = Path(os.getenv("LOG_PATH", str(BASE_DIR / "logs" / "service_requests.jsonl")))
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
MODEL_NAME: str = os.getenv("MODEL_NAME", "llama3.2:1b")
MODEL_DIGEST: str = os.getenv("MODEL_DIGEST", "")
RUN_ID: str = os.getenv("RUN_ID", "development")
MODEL_TIMEOUT: float = float(os.getenv("MODEL_TIMEOUT", "120"))
OUTPUT_FORMAT: str = "category-json-v1"


def get_db() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn: sqlite3.Connection = get_db()
    with closing(conn), conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            narrative TEXT NOT NULL,
            category TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
