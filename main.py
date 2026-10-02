from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import requests
import sqlite3
import datetime
import logging

app = FastAPI(title="Ticket Triage Service")

# Configure file logging for auditability
logging.basicConfig(
    filename='service_requests.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Database Setup
def get_db():
    conn = sqlite3.connect('tickets.db')
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            narrative TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

OLLAMA_URL = "http://ollama:11434/api/generate"
MODEL_NAME = "llama3.2:1b"

CATEGORIES = [
    "Credit reporting", "Debt collection", "Mortgage", 
    "Credit card", "Bank account or service", "Consumer loan", "Money transfer or service"
]

class TicketRequest(BaseModel):
    narrative: str

@app.post("/tickets")
def classify_ticket(ticket: TicketRequest):
    start_time = datetime.datetime.now()
    
    prompt = f"""You are a financial complaint classifier. Classify the following ticket into EXACTLY one of these categories:
{', '.join(CATEGORIES)}.

Respond with ONLY the exact category name and nothing else.

Ticket Narrative:
{ticket.narrative}"""

    # Synchronous call to Ollama backend
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }, timeout=120)
        
        category = response.json().get('response', '').strip()
        
        # Fallback handling for strict output conformance
        matched_cat = next((c for c in CATEGORIES if c.lower() in category.lower()), "Credit reporting")
        
    except Exception as e:
        logging.error(f"Inference error: {str(e)}")
        raise HTTPException(status_code=500, detail="Model backend error")

    # Store in SQLite database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tickets (narrative, category) VALUES (?, ?)", (ticket.narrative, matched_cat))
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()

    elapsed = (datetime.datetime.now() - start_time).total_seconds()
    logging.info(f"POST /tickets | ID: {ticket_id} | Category: {matched_cat} | Latency: {elapsed:.4f}s")
    
    return {"id": ticket_id, "category": matched_cat}

@app.get("/search")
def search_tickets(q: str = Query(..., min_length=1)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, narrative, category, created_at FROM tickets WHERE narrative LIKE ?", (f"%{q}%",))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "narrative": r[1], "category": r[2], "created_at": r[3]} for r in rows]

@app.get("/stats")
def get_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT category, COUNT(*) FROM tickets GROUP BY category")
    counts = dict(cursor.fetchall())
    conn.close()
    
    # Format to ensure all categories are returned
    return {cat: counts.get(cat, 0) for cat in CATEGORIES}