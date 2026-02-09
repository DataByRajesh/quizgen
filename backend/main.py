"""FastAPI backend for quizgen.

Endpoints:
- POST /upload -> accept file (pdf/docx/txt), extract text, return doc_id
- POST /generate -> generate MCQs using an LLM (OpenAI) for a given doc_id

Storage: in-memory dict `DOC_STORE` holds extracted text and metadata.
"""

import os
import uuid
import json
import time
import threading
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from time import sleep

try:
    # when running as package
    from . import db
except Exception:
    # when tests import this module as a top-level module (sys.path points to backend/)
    import db

try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    import docx
except Exception:
    docx = None

import openai

BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, "storage", "uploads")
EXTRACTED_DIR = os.path.join(BASE_DIR, "storage", "extracted")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXTRACTED_DIR, exist_ok=True)

app = FastAPI(title="quizgen-backend")

# Allow CORS from the frontend dev server(s)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compatibility: provide a DOC_STORE-like mapping for existing tests that expect an in-memory dict


class _DocStoreCompat:
    def __contains__(self, key: str) -> bool:
        return db.get_document(key) is not None

    def __getitem__(self, key: str) -> Dict[str, Any]:
        doc = db.get_document(key)
        if not doc:
            raise KeyError(key)
        return {"filename": doc.get("filename"), "text": doc.get("text")}


DOC_STORE = _DocStoreCompat()


# Configuration: optional API key auth and rate limiting
_API_KEYS = set([k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip()])
_RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "0"))

# in-memory token buckets: key -> {tokens, last_refill}
_buckets: Dict[str, Dict[str, float]] = {}
_bucket_lock = threading.Lock()


def _refill_bucket(key: str):
    if _RATE_LIMIT_PER_MIN <= 0:
        return
    now = time.time()
    with _bucket_lock:
        b = _buckets.get(key)
        if not b:
            _buckets[key] = {"tokens": float(_RATE_LIMIT_PER_MIN), "last": now}
            return
        elapsed = now - b["last"]
        # tokens to add
        add = elapsed * (_RATE_LIMIT_PER_MIN / 60.0)
        b["tokens"] = min(float(_RATE_LIMIT_PER_MIN), b["tokens"] + add)
        b["last"] = now


def _consume_token(key: str) -> bool:
    if _RATE_LIMIT_PER_MIN <= 0:
        return True
    _refill_bucket(key)
    with _bucket_lock:
        b = _buckets.setdefault(key, {"tokens": float(_RATE_LIMIT_PER_MIN), "last": time.time()})
        if b["tokens"] >= 1.0:
            b["tokens"] -= 1.0
            return True
        return False


def require_api_key(x_api_key: Optional[str] = Header(None)) -> Optional[str]:
    # If API_KEYS is not set, authentication is disabled (for tests/dev)
    if not _API_KEYS:
        return x_api_key or "__anon__"
    if not x_api_key or x_api_key not in _API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key


def rate_limit_dependency(api_key: Optional[str] = Depends(require_api_key)):
    # Use provided api_key (or __anon__) as bucket key
    key = api_key or "__anon__"
    if not _consume_token(key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return True


def extract_text_from_pdf(path: str) -> str:
    if not pdfplumber:
        raise RuntimeError("pdfplumber not installed")
    text_parts: List[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def extract_text_from_docx(path: str) -> str:
    if not docx:
        raise RuntimeError("python-docx not installed")
    doc = docx.Document(path)
    paragraphs = [p.text for p in doc.paragraphs]
    return "\n".join(paragraphs)


def extract_text_from_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def generate_dummy_mcqs(text: str, n: int) -> List[Dict[str, Any]]:
    # Very small deterministic fallback: create questions from first n sentences
    sentences = [s.strip() for s in text.replace("\n", " ").split('.') if s.strip()]
    mcqs = []
    for i in range(min(n, len(sentences))):
        q = sentences[i]
        mcqs.append({
            "question": f"What is the main idea of: {q}?",
            "options": [q, "Not related", "Partially related", "Opposite"],
            "answer_index": 0,
        })
    # If not enough sentences, pad with generic questions
    while len(mcqs) < n:
        mcqs.append({
            "question": "Generate a meaningful question from the document.",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer_index": 0,
        })
    return mcqs


def call_openai_generate(text: str, n: int) -> List[Dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    openai.api_key = api_key
    system = (
        "You are an assistant that generates multiple-choice questions (MCQs). "
        "Given an input document, produce exactly the requested number of questions. "
        "Return a JSON array only, where each element is an object with keys: "
        "'question' (string), 'options' (array of 4 strings), 'answer_index' (integer 0-3)."
    )

    user = (
        f"Document:\n" + text + "\n\n" + f"Generate {n} MCQs."
    )

    # Use ChatCompletion API with retries and validation
    max_attempts = 3
    backoff = 1.0
    for attempt in range(1, max_attempts + 1):
        try:
            resp = openai.ChatCompletion.create(
                model=os.getenv("MODEL", "gpt-4o-mini"),
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.0 if attempt > 1 else 0.2,
                max_tokens=1500,
            )
            content = resp.choices[0].message.content

            # Try parse and validate
            parsed = json.loads(content)
            validated = validate_mcqs(parsed)
            return validated[:n] if len(validated) >= n else (validated + generate_dummy_mcqs(text, n - len(validated)))
        except Exception:
            # If not last attempt, try a recovery request asking for JSON-only output
            if attempt < max_attempts:
                try:
                    recovery_prompt = (
                        "The previous response could not be parsed as JSON matching the required schema. "
                        "Respond with a JSON array only (no surrounding text). Each element must be an object with keys: "
                        "'question' (string), 'options' (array of 4 strings), 'answer_index' (integer 0-3)."
                    )
                    resp = openai.ChatCompletion.create(
                        model=os.getenv("MODEL", "gpt-4o-mini"),
                        messages=[{"role": "system", "content": system}, {"role": "user", "content": recovery_prompt + "\n\nOriginal document:\n" + text}],
                        temperature=0.0,
                        max_tokens=1500,
                    )
                    content = resp.choices[0].message.content
                    parsed = json.loads(content)
                    validated = validate_mcqs(parsed)
                    return validated[:n] if len(validated) >= n else (validated + generate_dummy_mcqs(text, n - len(validated)))
                except Exception:
                    sleep(backoff)
                    backoff *= 2
                    continue
            else:
                break
    # All attempts failed — fallback to deterministic generator
    return generate_dummy_mcqs(text, n)


class GenerateRequest(BaseModel):
    doc_id: str
    num_questions: int = 5


class MCQItem(BaseModel):
    question: str
    options: List[str]
    answer_index: int


def validate_mcqs(data: Any) -> List[Dict[str, Any]]:
    """Validate parsed JSON against the MCQItem schema and return list of dicts.

    Raises ValueError if validation fails.
    """
    if not isinstance(data, list):
        raise ValueError("MCQ response is not a list")
    validated: List[Dict[str, Any]] = []
    for idx, item in enumerate(data):
        try:
            mcq = MCQItem(**item)
            # enforce exactly 4 options
            if len(mcq.options) != 4:
                raise ValueError(f"item {idx} must have 4 options")
            if not (0 <= mcq.answer_index < 4):
                raise ValueError(f"item {idx} answer_index out of range")
            # Use model_dump for Pydantic v2 compatibility
            validated.append(mcq.model_dump())
        except Exception as e:
            raise ValueError(f"Invalid MCQ item at index {idx}: {e}")
    return validated


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), _auth=Depends(rate_limit_dependency)):
    # Save uploaded file to disk
    contents = await file.read()
    doc_id = str(uuid.uuid4())
    filename = f"{doc_id}_{file.filename}"
    save_path = os.path.join(UPLOAD_DIR, filename)
    with open(save_path, "wb") as f:
        f.write(contents)

    # Extract text based on extension
    ext = os.path.splitext(file.filename)[1].lower()
    try:
        if ext == ".pdf":
            text = extract_text_from_pdf(save_path)
        elif ext in (".docx", ".doc"):
            text = extract_text_from_docx(save_path)
        else:
            # treat as txt
            text = extract_text_from_txt(save_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {e}")

    # persist extracted text to disk and to SQLite DB
    extracted_path = os.path.join(EXTRACTED_DIR, f"{doc_id}.txt")
    with open(extracted_path, "w", encoding="utf-8") as ef:
        ef.write(text)

    # store in sqlite DB
    db.create_document(doc_id=doc_id, filename=file.filename, upload_path=save_path, extracted_path=extracted_path, text=text)

    return JSONResponse({"doc_id": doc_id})


@app.post("/generate")
async def generate_mcqs(req: GenerateRequest, _auth=Depends(rate_limit_dependency)):
    doc = db.get_document(req.doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="doc_id not found")
    text = doc.get("text", "")
    # Try using OpenAI if configured, otherwise fallback
    try:
        mcqs = call_openai_generate(text, req.num_questions)
    except Exception:
        mcqs = generate_dummy_mcqs(text, req.num_questions)

    return JSONResponse({"doc_id": req.doc_id, "mcqs": mcqs})


@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
