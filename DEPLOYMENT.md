# Deployment notes

This project includes a frontend (Next.js) and a backend (FastAPI). Below are quick deployment options and what you'll need to configure.

Frontend (Recommended: Vercel)
- Create a Vercel project and connect the `frontend/` directory or the repository.
- Vercel auto-detects Next.js and will run `npm install` and `npm run build`.
- No special environment variables are required for the build. For runtime configuration (e.g., pointing to a self-hosted backend), set `NEXT_PUBLIC_API_URL` in Vercel Environment Variables.

Backend (Options)
- Render / Railway / Fly / Heroku: deploy the `backend/` folder as a Python service.
  - Set `OPENAI_API_KEY` as a secret/env var in the platform.
  - Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

CI Deployment (manual)
- The repository includes a CI workflow that runs tests and builds the frontend. To add automated deploy steps:
  - For Vercel: use `vercel/action@v1` or the `amondnet/vercel-action` and provide `VERCEL_TOKEN` as a secret.
  - For Render/Railway: use the platform's CLI in the workflow and provide an API key as a secret.

  Render
  - Create a service on Render and note the `SERVICE ID` for the service you want to trigger a deploy for.
  - In GitHub, add repository secrets:
    - `RENDER_API_KEY` — your Render API key
    - `RENDER_SERVICE_ID` — the service id to trigger deploys for
  - The CI workflow triggers a deploy by calling the Render API:
    ```bash
    curl -X POST "https://api.render.com/v1/services/${RENDER_SERVICE_ID}/deploys" \
      -H "Authorization: Bearer ${RENDER_API_KEY}" \
      -H "Content-Type: application/json" \
      -d '{}'
    ```

  Railway
  - Create a Railway project and obtain an API token and the project id.
  - In GitHub, add repository secrets:
    - `RAILWAY_TOKEN` — your Railway API token
    - `RAILWAY_PROJECT_ID` — the Railway project id to deploy
  - The CI workflow uses the Railway CLI to login and run a deploy (the workflow installs `@railway/cli` and runs `railway up`). See Railway docs for project-specific usage.

Security
- Never commit `OPENAI_API_KEY` to the repository. Use platform secrets.

If you'd like, I can add a sample `deploy` job to the CI that deploys to Vercel using a `VERCEL_TOKEN` secret — tell me which provider you'd like and I will add a sample job.
