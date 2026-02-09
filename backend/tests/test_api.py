import os
import io
import sys
import pytest

from httpx import AsyncClient, ASGITransport

# Ensure backend package can be imported when tests are run from project root
TEST_BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
if TEST_BACKEND_DIR not in sys.path:
    sys.path.insert(0, TEST_BACKEND_DIR)

from main import app, UPLOAD_DIR, EXTRACTED_DIR
import db


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/health")
        assert r.status_code == 200
        assert r.json().get("status") == "ok"


@pytest.mark.asyncio
async def test_upload_and_generate_txt(tmp_path):
    # prepare a small txt file
    content = "This is a test document. It contains information about testing.\nSecond sentence."
    file_bytes = content.encode("utf-8")

    files = {"file": ("test.txt", io.BytesIO(file_bytes), "text/plain")}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        up = await ac.post("/upload", files=files)
        assert up.status_code == 200
        data = up.json()
        doc_id = data.get("doc_id")
        assert doc_id is not None

        # Ensure stored in sqlite DB
        stored = db.get_document(doc_id)
        assert stored is not None

        gen = await ac.post("/generate", json={"doc_id": doc_id, "num_questions": 2})
        assert gen.status_code == 200
        body = gen.json()
        assert body.get("doc_id") == doc_id
        mcqs = body.get("mcqs")
        assert isinstance(mcqs, list)
        assert len(mcqs) == 2
