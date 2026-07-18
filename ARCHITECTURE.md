# Architecture

## Design goals

The assignment asks for a small journal application, but journals contain sensitive data and LLM calls are costly. The implementation therefore keeps the required API shapes while adding authentication, authorization, strict validation, deterministic aggregation, and cache-aware analysis.

## Request flow

1. A user registers or logs in and receives a signed JWT.
2. The Next.js client calls a same-origin server route, so the backend origin stays server-configured.
3. FastAPI validates the token and derives the user identity server-side.
4. Journal reads and writes are filtered by that authenticated identity. Assignment-compatible `userId` values are accepted only when they match the token.
5. Analysis accepts either the PDF's raw `text` shape or the safer UI `entryId` shape. For an entry ID, the backend verifies ownership and loads the stored text.
6. Normalized text is hashed with SHA-256. An existing analysis is reused before an LLM call is attempted.
7. Groq returns a strict JSON-schema response with a controlled emotion label, three to five grounded keywords, and one neutral summary sentence.
8. The validated result is persisted, and insights are calculated deterministically from the authenticated user's entries.

## Components

- **Next.js frontend:** account flow, journal composer, history, analysis cards, and longitudinal insights.
- **Next.js proxy:** forwards API requests and bearer tokens to a server-configured backend origin.
- **FastAPI routes:** validation, authentication, authorization, compatibility aliases, response contracts, and safe error mapping.
- **CRUD layer:** SQLAlchemy persistence, ordered queries, and integrity-conflict handling.
- **Analysis service:** isolated Groq integration using strict structured output and a controlled emotion taxonomy.
- **Insights service:** deterministic aggregation over stored analyses; it never asks the LLM to calculate statistics.
- **PostgreSQL:** durable production storage through Neon. SQLite remains available for local development and previews.

## Data model

- `users`: username, scrypt password hash, creation timestamp.
- `journal_entries`: authenticated owner, ambience, raw journal text, creation timestamp.
- `journal_analyses`: one analysis per entry, normalized-text hash, emotion, JSON keywords, summary.

Foreign keys prevent journals from referencing missing users and analyses from referencing missing entries. A unique constraint prevents multiple analysis rows for one entry. The text hash allows analysis reuse when the same reflection appears more than once.

## LLM contract

The model cannot return arbitrary prose. Groq Structured Outputs constrains the response to the API schema, and Pydantic validates it again before persistence.

- Emotion is one of 12 stable labels, keeping insight aggregation meaningful.
- Keywords must contain three to five unique, concise themes grounded in the entry.
- Summary is a short, neutral observation rather than advice or diagnosis.
- The model receives only the journal text and ambience needed for the requested analysis.
- Authentication/configuration errors are separated from transient provider failures without returning provider response bodies to clients.

## Security boundaries

- The verified token, not request JSON, is the source of truth for ownership.
- A mismatched assignment-style `userId` receives `403`.
- A user cannot read or analyze another user's entry.
- Production requires a strong JWT secret and durable `DATABASE_URL`.
- Passwords use memory-hard scrypt hashes; secrets stay in environment variables.
- Journal payloads reject empty text, unknown fields, unsupported ambience values, and oversized content.
- AI output is treated as untrusted data and schema-validated before storage.

## 1. How would you scale this to 100k users?

The current stateless FastAPI service and PostgreSQL database are a good starting boundary. At 100k users I would:

1. Run multiple API instances behind a load balancer and pool PostgreSQL connections through PgBouncer.
2. Add Alembic migrations, database indexes for `(user_id, created_at)` and text hashes, read replicas for journal history, and pagination rather than returning an unbounded list.
3. Move LLM analysis to a durable queue. The POST would return `202 Accepted` with a job ID; workers would process independently and clients could poll or receive server-sent events.
4. Precompute per-user insight snapshots when an analysis completes instead of scanning a user's history on every request.
5. Add Redis for distributed rate limits, short-lived job state, and hot insight reads.
6. Add structured logs, tracing, latency/error SLOs, dead-letter queues, and autoscaling based on API latency and queue depth.

## 2. How would you reduce LLM cost?

1. Keep the existing normalized-text hash cache so duplicate content never produces a second paid call.
2. Use a small structured-output model for classification and reserve larger models for explicit deeper reflection features.
3. Cap input length and output tokens, use a controlled taxonomy, and avoid asking the LLM to calculate deterministic insights.
4. Batch or defer non-urgent analysis through workers and enforce per-user quotas.
5. Track prompt tokens, completion tokens, cache-hit ratio, and cost per analyzed entry so optimization is evidence-led.

## 3. How would you cache repeated analysis?

The current application hashes normalized journal text with SHA-256 and looks up an existing stored analysis before calling Groq. A cache hit is copied to the owned entry so reads remain simple.

At scale I would separate this into an `analysis_cache` table keyed by `(model_version, prompt_version, text_hash)`. Including versions prevents stale results after a prompt or model change. Redis could hold the hottest results, while PostgreSQL remains the durable source of truth. A short distributed lock around a cache miss would prevent two workers from analyzing identical text simultaneously.

## 4. How would you protect sensitive journal data?

1. Encrypt traffic with TLS and use provider-managed encryption at rest; for higher assurance, envelope-encrypt journal text with a per-user data key managed by a cloud KMS.
2. Keep authorization checks server-side, use short-lived sessions in secure HTTP-only cookies, rotate signing keys, and add account recovery with step-up verification.
3. Apply least-privilege database and deployment roles, isolate production secrets, and never log journal text or provider credentials.
4. Add audit logs for access and deletion, retention controls, user export/deletion workflows, encrypted backups, and tested restore procedures.
5. Redact or minimize data before external LLM calls, document the provider boundary, and offer a no-AI mode for users who prefer local storage only.

## Trade-offs

- The assignment's `/:userId` routes remain available, but require authentication and a matching identity. This preserves compatibility without enabling insecure cross-user access.
- The UI analyzes stored entries by ID instead of resending text, preventing a client from analyzing one string while attaching the result to another entry.
- Table creation at startup is acceptable for the take-home scope; Alembic is the next production step.
- Synchronous analysis keeps the demo simple, while a queue is the clear scaling path.
