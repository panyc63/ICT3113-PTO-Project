"""GET /search: find stored narratives matching the supplied query."""
from contextlib import closing
import sqlite3
from typing import Any

from fastapi import APIRouter, Query

from api import runtime

router: APIRouter = APIRouter()


@router.get("/search")
def search_tickets(q: str = Query(..., min_length=1)) -> list[dict[str, Any]]:
    conn: sqlite3.Connection = runtime.get_db()
    with closing(conn):
        rows: list[tuple[int, str, str, str]] = conn.execute(
            "SELECT id, narrative, category, created_at FROM tickets WHERE narrative LIKE ?",
            (f"%{q}%",),
        ).fetchall()
    return [dict(zip(("id", "narrative", "category", "created_at"), row)) for row in rows]
