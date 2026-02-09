# quizgen

Full-stack scaffold for a Quiz Generator: upload documents, extract text, generate MCQs using an LLM.

## Structure

quizgen/
  backend/
    main.py
    requirements.txt
    .env.example
    storage/uploads/.gitkeep
    storage/extracted/.gitkeep

  frontend/
    README.md (placeholder for Next.js app)

  .gitignore
  README.md

## Next steps

1. Initialize the frontend Next.js app:

```powershell
npx create-next-app@latest frontend --ts --experimental-app
```

2. Implement backend endpoints in `backend/main.py` (POST /upload, POST /generate).
3. Wire frontend to backend and configure OPENAI_API_KEY in `.env`.