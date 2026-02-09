import asyncio
import io
import os
import sys
from httpx import AsyncClient, ASGITransport

# allow importing backend.main when running script from project root
TEST_BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
if TEST_BACKEND_DIR not in sys.path:
    sys.path.insert(0, TEST_BACKEND_DIR)

from main import app

async def main():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/health")
        print('/health', r.status_code, r.json())

        content = "This is a demo document.\nSecond line."
        files = {"file": ("test.txt", io.BytesIO(content.encode('utf-8')), "text/plain")}
        up = await ac.post('/upload', files=files)
        print('/upload', up.status_code, up.json())
        doc_id = up.json().get('doc_id')

        gen = await ac.post('/generate', json={'doc_id': doc_id, 'num_questions': 2})
        print('/generate', gen.status_code, gen.json())

        docs = await ac.get('/documents')
        print('/documents', docs.status_code, docs.json())

if __name__ == '__main__':
    asyncio.run(main())
