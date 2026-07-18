# AI-Assisted Journal System

A secure full-stack take-home project for storing private nature-session reflections, analyzing emotional tone with a Groq-hosted LLM, and viewing patterns over time.

**Live demo:** [ai-journal-system-fawn.vercel.app](https://ai-journal-system-fawn.vercel.app)

The implementation deliberately goes beyond the assignment's minimum: it preserves the requested API shapes while adding authentication, user isolation, strict structured LLM output, durable PostgreSQL storage, analysis caching, and CI. See [ASSIGNMENT_REVIEW.md](ASSIGNMENT_REVIEW.md) for the requirement-by-requirement audit and [ARCHITECTURE.md](ARCHITECTURE.md) for design trade-offs and scaling answers.

## Features

- Account registration and login with signed JWT access tokens
- Password hashing with Python's memory-hard `scrypt` implementation
- Authenticated, user-isolated journal storage
- Strict Pydantic validation for journal and authentication inputs
- Server-controlled LLM analysis: clients send an entry ID, never trusted journal text
- Schema-constrained emotion, keyword, and summary generation through Groq
- Controlled emotion taxonomy and non-diagnostic wellness prompt
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
| AI | Groq Chat Completions API, GPT-OSS 20B structured output |
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

Set a current `GROQ_API_KEY` and a strong `JWT_SECRET` in `backend/.env`. `GROQ_MODEL` defaults to `openai/gpt-oss-20b` and may be overridden. The app is available at `http://localhost:3000`, and FastAPI documentation is at `http://localhost:8000/docs`.

The authentication/database schema is intentionally incompatible with databases created by the original unauthenticated prototype. Back up any local journal data and start with a new `journal.db` when upgrading.

## Docker Compose

```bash
cp .env.example .env
# Set GROQ_API_KEY and a random JWT_SECRET of at least 32 characters.
docker compose up -d --build
```

The frontend runs on port `3000`, the backend on `8000`, and SQLite data persists in the `backend_data` volume at `/data` without hiding application code.

## Vercel deployment

Configure the frontend project with `frontend` as its root directory and set
`BACKEND_URL` to the deployed backend origin. Configure the backend project with
`backend` as its root directory and store `GROQ_API_KEY` and `JWT_SECRET` in the
project environment.

Production requires a managed PostgreSQL connection in `DATABASE_URL`; the
backend refuses to start without one so accounts and journals cannot silently
fall back to disposable storage. Local development and Vercel previews may use
SQLite when `DATABASE_URL` is unset.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/auth/register` | Create an account and receive a token |
| POST | `/api/auth/login` | Authenticate and receive a token |
| POST | `/api/journal` | Create a journal entry |
| GET | `/api/journal` | List the authenticated user's entries |
| POST | `/api/journal/analyze` | Analyze an owned entry by ID |
| GET | `/api/journal/insights` | View authenticated-user insights |
| GET | `/api/journal/{userId}` | Assignment-compatible authorized alias |
| GET | `/api/journal/insights/{userId}` | Assignment-compatible authorized alias |

Journal endpoints require `Authorization: Bearer <token>`. The analysis endpoint accepts exactly one of `{"entryId": 42}` or the assignment-compatible `{"text": "..."}`. The UI uses `entryId` so the backend—not the browser—selects the stored text.

## Interview demo path

1. Register two users and show that one cannot read the other's journal.
2. Save a nature-session reflection and analyze it.
3. Point out the controlled emotion label, grounded keyword chips, and neutral summary.
4. Save the same text in another entry and show the cached response path.
5. Open `/docs` to discuss typed contracts, compatibility routes, and error responses.
6. Use `ARCHITECTURE.md` to discuss the 100k-user, LLM-cost, cache, and privacy trade-offs.

## Verification

```bash
cd backend
pip install -r requirements-dev.txt
ruff check app tests
pytest -q --cov=app --cov-report=term-missing --cov-fail-under=85

cd ../frontend
npm ci
npm run lint
npm run build
npm audit

# With both local services running, or pass a deployed proxy URL:
cd ..
./scripts/smoke-test.sh
./scripts/smoke-test.sh https://your-frontend.example/api/proxy
```

## Production roadmap

- Add Alembic migrations for future PostgreSQL schema changes.
- Store authentication in secure HTTP-only cookies when frontend and API share a production domain.
- Move LLM work to a background queue for lower API latency.
- Add rate limiting, account recovery, journal deletion, audit logging, and encrypted backups.
- Precompute insights and add observability before scaling horizontally.
