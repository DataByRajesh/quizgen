Deploying the quizgen backend
=============================

This file shows quick instructions to deploy the backend (FastAPI app) using Docker, Render.com, or Railway.

Prerequisites
-------------
- A GitHub repository with this project (already present)
- Docker (for local builds) or a cloud provider account (Render/Railway)

Docker (local)
--------------
Build and run the backend locally with Docker:

```powershell
cd "C:\path\to\quizgen"
docker build -t quizgen-backend -f backend/Dockerfile .
docker run -p 8000:8000 -e PORT=8000 --rm quizgen-backend
```

Render (one-click / CLI)
------------------------
The repository includes `render.yaml` which tells Render to use the `backend/Dockerfile` to build the service.

1. Go to https://dashboard.render.com
2. Create a new Web Service -> Connect your GitHub repo -> Select `quizgen` repo -> Choose branch `main`.
3. Render will detect the `render.yaml` and build the Docker image.

Railway
-------
Railway supports Docker-based deploys or using the CLI. You can either:

- Use the Dockerfile above and push to Railway as a Docker service.
- Or create a new project and set the start command to:

  ```text
  uvicorn backend.main:app --host 0.0.0.0 --port $PORT
  ```

Environment variables
---------------------
- `OPENAI_API_KEY` - (optional) for real LLM generation.
- `API_KEYS` - (optional) comma-separated API keys to enable auth.
- `RATE_LIMIT_PER_MIN` - (optional) integer rate limit per minute.
- `QUIZGEN_DB_PATH` - (optional) override DB file path.
