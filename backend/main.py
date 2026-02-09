"""FastAPI backend for quizgen.

Endpoints:
- POST /upload -> accept file (pdf/docx/txt), extract text, return doc_id
- POST /generate -> generate MCQs using an LLM (OpenAI) for a given doc_id

Storage: in-memory dict `DOC_STORE` holds extracted text and metadata.
"""

import os
import uuid
import json
from typing import Dict, Any, List

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

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

# Simple in-memory store: doc_id -> {filename, text}
DOC_STORE: Dict[str, Dict[str, Any]] = {}


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

    # Use ChatCompletion API
    resp = openai.ChatCompletion.create(
        model=os.getenv("MODEL", "gpt-4o-mini"),
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.2,
        max_tokens=1500,
    )
    content = resp.choices[0].message.content

    # Expect JSON array; try to parse
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        raise ValueError("OpenAI did not return a list")
    except Exception:
        # Fallback: return dummy MCQs if parse fails
        return generate_dummy_mcqs(text, n)


class GenerateRequest(BaseModel):
    doc_id: str
    num_questions: int = 5


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
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

    # store in-memory and write extracted text to disk
    DOC_STORE[doc_id] = {"filename": file.filename, "text": text}
    extracted_path = os.path.join(EXTRACTED_DIR, f"{doc_id}.txt")
    with open(extracted_path, "w", encoding="utf-8") as ef:
        ef.write(text)

    return JSONResponse({"doc_id": doc_id})


@app.post("/generate")
async def generate_mcqs(req: GenerateRequest):
    if req.doc_id not in DOC_STORE:
        raise HTTPException(status_code=404, detail="doc_id not found")
    text = DOC_STORE[req.doc_id]["text"]
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
