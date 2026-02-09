import os
import threading
import uuid

import pytest

TEST_BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
if TEST_BACKEND_DIR not in __import__('sys').path:
    __import__('sys').path.insert(0, TEST_BACKEND_DIR)

import db


def test_create_and_get_document(tmp_path):
    # Use a temporary DB for isolation
    db_path = tmp_path / "test_quizgen.db"
    os.environ["QUIZGEN_DB_PATH"] = str(db_path)
    # reload module to pick up new DB path
    import importlib
    importlib.reload(db)

    doc_id = str(uuid.uuid4())
    db.create_document(doc_id, "f.txt", "/tmp/upload", "/tmp/extracted", "text content")
    got = db.get_document(doc_id)
    assert got is not None
    assert got["id"] == doc_id
    assert got["filename"] == "f.txt"


def test_get_missing_document():
    got = db.get_document("non-existent-id")
    assert got is None


def test_concurrent_creates(tmp_path):
    db_path = tmp_path / "concurrent.db"
    os.environ["QUIZGEN_DB_PATH"] = str(db_path)
    import importlib
    importlib.reload(db)

    created = []

    def worker(i):
        did = str(uuid.uuid4())
        db.create_document(did, f"file{i}", f"/u/{i}", f"/e/{i}", f"text{i}")
        created.append(did)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # ensure all created documents are present
    for did in created:
        assert db.get_document(did) is not None
