"""GET /stats: report counts for all seven ticket categories."""
from contextlib import closing
import sqlite3

from fastapi import APIRouter

from api import runtime
from categories import CATEGORIES

router: APIRouter = APIRouter()


@router.get("/stats")
def get_stats() -> dict[str, int]:
    conn: sqlite3.Connection = runtime.get_db()
    with closing(conn):
        counts: dict[str, int] = dict(conn.execute("SELECT category, COUNT(*) FROM tickets GROUP BY category"))
    return {category: counts.get(category, 0) for category in CATEGORIES}
