# Deployment Plan for QuizGen App

## Status Update
- Code is ready: Frontend built and linted, backend tested (9/9 tests pass), servers run locally.
- Frontend: Next.js app with upload/generate page and documents management.
- Backend: FastAPI with endpoints for upload, generate MCQs, list documents, etc.
- Fixed: TypeScript lint error in frontend.

## Quick Deploy Instructions (ASAP)
1. **Push to GitHub**: Create a GitHub repo and push the `quizgen/` folder.
2. **Deploy Backend to Render**:
   - Go to [render.com](https://render.com), sign up/login.
   - Click "New" > "Web Service".
   - Connect your GitHub repo, select `quizgen` repo.
   - Set build type to "Docker", root directory `/` (uses render.yaml).
   - Set environment variable: `OPENAI_API_KEY` = your OpenAI API key.
   - Deploy; note the URL (e.g., https://quizgen-backend.onrender.com).
3. **Deploy Frontend to Vercel**:
   - Go to [vercel.com](https://vercel.com), sign up/login.
   - Click "New Project", connect GitHub repo.
   - Select `frontend/` as root directory.
   - Set environment variable: `NEXT_PUBLIC_API_URL` = Render backend URL (e.g., https://quizgen-backend.onrender.com).
   - Deploy; note the URL (e.g., https://quizgen.vercel.app).
4. **Test Live**: Visit Vercel URL, upload a document, generate MCQs.

## Optional: Automated CI Deploys
- Set GitHub secrets: VERCEL_TOKEN, RENDER_API_KEY, RENDER_SERVICE_ID, OPENAI_API_KEY.
- Push to main branch to auto-deploy via CI workflow.

## Followup Steps
- Verify full flow: Upload doc, generate MCQs, view in documents page.
- If issues, check Render/Vercel logs.
