# AI-Assisted Journal System

A secure full-stack journal application for storing private reflections, analyzing emotions with a Groq-hosted LLM, and viewing mental-state insights over time.

## Features

- Account registration and login with signed JWT access tokens
- Password hashing with Python's memory-hard `scrypt` implementation
- Authenticated, user-isolated journal storage
- Strict Pydantic validation for journal and authentication inputs
- Server-controlled LLM analysis: clients send an entry ID, never trusted journal text
- Emotion, keyword, and summary generation through Groq
- SHA-256 text-hash caching to avoid repeated LLM calls
- Per-user insights for entry count, top emotion, ambience, and recent keywords
- Responsive Next.js frontend with an internal backend proxy
- Docker Compose deployment with persistent SQLite data and health checks
- Automated backend tests, linting, frontend build verification, and GitHub Actions CI

## Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Backend | FastAPI, Pydantic, SQLAlchemy |
| Database | SQLite locally; PostgreSQL-ready through `DATABASE_URL` |
| AI | Groq Chat Completions API |
| Security | JWT, scrypt password hashing, authorization checks |
| Quality | Pytest, Ruff, ESLint, GitHub Actions |

## Local development

Requirements: Node.js 20+, Python 3.11+, and a Groq API key.

```bash
cp backend/.env.example backend/.env
npm install
cd frontend && npm install && cd ..
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-dev.txt
npm run dev
```

Set `GROQ_API_KEY` and a strong `JWT_SECRET` in `backend/.env`. The app is available at `http://localhost:3000`, and FastAPI documentation is at `http://localhost:8000/docs`.

The authentication/database schema is intentionally incompatible with databases created by the original unauthenticated prototype. Back up any local journal data and start with a new `journal.db` when upgrading.

## Docker Compose

```bash
cp .env.example .env
# Set GROQ_API_KEY and a random JWT_SECRET of at least 32 characters.
docker compose up -d --build
```

The frontend runs on port `3000`, the backend on `8000`, and SQLite data persists in the `backend_data` volume at `/data` without hiding application code.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/auth/register` | Create an account and receive a token |
| POST | `/api/auth/login` | Authenticate and receive a token |
| POST | `/api/journal` | Create a journal entry |
| GET | `/api/journal` | List the authenticated user's entries |
| POST | `/api/journal/analyze` | Analyze an owned entry by ID |
| GET | `/api/journal/insights` | View authenticated-user insights |

Journal endpoints require `Authorization: Bearer <token>`.

## Verification

```bash
cd backend
pip install -r requirements-dev.txt
ruff check app tests
pytest -q

cd ../frontend
npm ci
npm run lint
npm run build
npm audit --omit=dev
```

## Production roadmap

- Replace SQLite with PostgreSQL and add Alembic migrations.
- Store authentication in secure HTTP-only cookies when frontend and API share a production domain.
- Move LLM work to a background queue for lower API latency.
- Add rate limiting, account recovery, journal deletion, audit logging, and encrypted backups.
- Precompute insights and add observability before scaling horizontally.
