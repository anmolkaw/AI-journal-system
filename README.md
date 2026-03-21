# AI-Assisted Journal System

A full-stack journal application for ArvyaX users to store post-session journal entries, analyze emotions using an LLM, and view mental-state insights over time.

## Features

- Create journal entries
- Retrieve all entries for a user
- Analyze journal text using a real LLM
- View aggregated insights:
  - total entries
  - top emotion
  - most used ambience
  - recent keywords
- Cache repeated analysis results using text hashing
- Minimal frontend to create, analyze, and view entries

## Tech Stack

### Backend
- FastAPI
- SQLAlchemy
- SQLite
- Groq API (LLM)

### Frontend
- Next.js
- React
- Tailwind CSS

## Project Structure

```bash
AI-journal-system/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── crud.py
│   │   ├── llm.py
│   │   ├── services/
│   │   │   ├── analysis_service.py
│   │   │   └── insights_service.py
│   │   └── utils/
│   │       └── hash.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── app/
│   ├── lib/
│   └── package.json
├── docker-compose.yml
├── package.json
├── README.md
└── ARCHITECTURE.md
```

## Local Development

1. Install dependencies:
   - root: `npm install`
   - frontend: `cd frontend && npm install`
   - backend (Python): `pip install -r backend/requirements.txt`
2. Add backend env vars in `backend/.env` (at minimum `GROQ_API_KEY`).
3. Run both services from repo root:

```bash
npm run dev
```

## Deployment (Docker Compose)

1. Create a `.env` file in the repo root:

```env
GROQ_API_KEY=your_groq_api_key
# Optional overrides
BACKEND_URL=http://backend:8000
CORS_ORIGINS=http://localhost:3000
```

2. Build and start the stack:

```bash
./scripts/deploy.sh
```

(Equivalent manual command: `docker compose up -d --build`.)

3. Access the app:
   - Frontend: `http://localhost:3000`
   - Backend health check: `http://localhost:8000/`

4. Stop the deployment:

```bash
docker compose down
```
