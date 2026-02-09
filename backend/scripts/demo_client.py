import time
import httpx

base = 'http://127.0.0.1:8000'
print('waiting a bit for server...')
for i in range(10):
    try:
        r = httpx.get(base + '/health', timeout=2.0)
        print('health', r.status_code, r.json())
        break
    except Exception as e:
        print('not ready yet:', e)
        time.sleep(1)

# upload a small txt
files = {'file': ('test.txt', 'This is a demo document.\nSecond line.', 'text/plain')}
with httpx.Client() as c:
    up = c.post(base + '/upload', files=files, timeout=10.0)
    print('/upload', up.status_code, up.text)
    doc_id = up.json().get('doc_id') if up.status_code == 200 else None
    if doc_id:
        gen = c.post(base + '/generate', json={'doc_id': doc_id, 'num_questions': 2}, timeout=30.0)
        print('/generate', gen.status_code, gen.text)

    docs = c.get(base + '/documents')
    print('/documents', docs.status_code, docs.text)
