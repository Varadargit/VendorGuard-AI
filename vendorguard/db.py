import json
import sqlite3
from .config import load_settings

def _connect():
    return sqlite3.connect(load_settings()["database_path"])

def init_db():
    with _connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            vendor_name TEXT NOT NULL,
            tax_id TEXT NOT NULL,
            status TEXT NOT NULL,
            vendor_json TEXT NOT NULL,
            result_json TEXT NOT NULL
        )""")
        conn.commit()

def save_run(vendor: dict, result: dict) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO runs(created_at, vendor_name, tax_id, status, vendor_json, result_json) VALUES(?,?,?,?,?,?)",
            (result["created_at"], vendor.get("vendor_name", ""), vendor.get("tax_id", "").strip().upper(), result["status"], json.dumps(vendor), json.dumps(result))
        )
        conn.commit()
        return cur.lastrowid

def find_duplicate_tax_id(tax_id: str):
    key = (tax_id or "").strip().upper()
    if not key:
        return None
    with _connect() as conn:
        row = conn.execute("SELECT id FROM runs WHERE upper(tax_id)=? ORDER BY id DESC LIMIT 1", (key,)).fetchone()
    return row[0] if row else None

def list_runs(limit=100):
    with _connect() as conn:
        rows = conn.execute("SELECT id, created_at, vendor_name, tax_id, status FROM runs ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
    return [{"id": r[0], "created_at": r[1], "vendor_name": r[2], "tax_id": r[3], "status": r[4]} for r in rows]

def get_run(run_id):
    with _connect() as conn:
        row = conn.execute("SELECT vendor_json, result_json FROM runs WHERE id=?", (int(run_id),)).fetchone()
    if not row:
        return None
    return {"vendor": json.loads(row[0]), "result": json.loads(row[1])}
