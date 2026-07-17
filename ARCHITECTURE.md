# Architecture

## Request flow

1. A user registers or logs in and receives a signed JWT.
2. The Next.js client sends the token through its same-origin proxy.
3. FastAPI validates the token and derives the user identity server-side.
4. Journal reads and writes are filtered by the authenticated identity.
5. Analysis accepts only an entry ID; the backend verifies ownership and loads the text.
6. The backend hashes normalized text and reuses an existing analysis when available.
7. Otherwise, Groq returns a schema-validated emotion, keyword list, and summary.
8. Per-user insights are calculated from authorized journal and analysis records.

## Components

- **Next.js frontend:** authentication, journal form, history, analysis actions, and insights.
- **Next.js proxy:** forwards API requests and bearer tokens to the private backend URL.
- **FastAPI routes:** validation, authentication, authorization, response contracts, and error mapping.
- **CRUD layer:** SQLAlchemy persistence and integrity-conflict handling.
- **Analysis service:** isolated LLM integration with strict output validation.
- **Insight service:** deterministic aggregation over stored records.
- **SQLite:** local and single-instance persistence. `DATABASE_URL` allows a future PostgreSQL move.

## Data model

- `users`: username, scrypt password hash, creation timestamp.
- `journal_entries`: authenticated owner, ambience, raw journal text, creation timestamp.
- `journal_analyses`: one analysis per entry, text hash, emotion, JSON keywords, summary.

Foreign keys prevent journals from referencing missing users and analyses from referencing missing entries. A unique constraint prevents multiple analysis rows for one entry.

## Security boundaries

- The client cannot select a `user_id`; identity comes from the verified token.
- A user receives `404` when attempting to analyze an entry they do not own.
- Raw exception and Groq response bodies are not returned to clients.
- Production startup rejects a JWT secret shorter than 32 characters.
- Docker persists only `/data`; application source remains immutable inside the image.
- Journal payloads reject empty text, unknown fields, unsupported ambience values, and oversized content.

## Scaling path

For larger production workloads, replace SQLite with PostgreSQL, add Alembic migrations, move LLM analysis to a queue-backed worker, use Redis for distributed cache/rate limiting, precompute insights, and deploy multiple API instances behind a load balancer. Add structured logging, latency/error metrics, encrypted backups, retention controls, and access auditing for sensitive journal data.
