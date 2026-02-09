import os
import sqlite3
import threading
import datetime

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "storage", "quizgen.db")
_lock = threading.Lock()


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            filename TEXT,
            upload_path TEXT,
            extracted_path TEXT,
            text TEXT,
            uploaded_at TEXT
        )
        """
        )
        conn.commit()
        conn.close()


def get_conn():
    # allow cross-thread connections in uvicorn workers
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def create_document(doc_id: str, filename: str, upload_path: str, extracted_path: str, text: str) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO documents (id, filename, upload_path, extracted_path, text, uploaded_at) VALUES (?,?,?,?,?,?)",
        (doc_id, filename, upload_path, extracted_path, text, datetime.datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_document(doc_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, filename, upload_path, extracted_path, text, uploaded_at FROM documents WHERE id=?",
        (doc_id,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "filename": row[1],
        "upload_path": row[2],
        "extracted_path": row[3],
        "text": row[4],
        "uploaded_at": row[5],
    }


# initialize DB on import
init_db()
