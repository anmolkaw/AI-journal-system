## System Overview

The system is a full-stack AI-assisted journaling application for ArvyaX users.

### Flow

1. User completes a nature session such as forest, ocean, or mountain
2. User writes a journal entry from the frontend
3. Backend stores the entry in SQLite
4. User clicks **Analyze**
5. Backend checks whether the text was analyzed before
6. If cached, the stored result is reused
7. If not cached, the backend calls the Groq LLM
8. The analysis result is stored in the database
9. Insights are computed from stored entries and analyses

---

## Current Architecture

### Frontend

- Next.js frontend with one page
- Displays:
  - journal entry form
  - previous entries
  - analyze action
  - insights
- Uses internal proxy API routes to communicate with backend

### Backend

- FastAPI REST API
- SQLAlchemy models and CRUD layer
- Service layer for:
  - analysis
  - insights
- Utility layer for hashing

### Database

- SQLite for local development and simple setup

### LLM

- Groq API for real-time text analysis

---

## Data Model

### `journal_entries`

Stores the raw user journal entry.

Fields:

- `id`
- `user_id`
- `ambience`
- `text`
- `created_at`

### `journal_analyses`

Stores the derived analysis result.

Fields:

- `id`
- `journal_entry_id`
- `text_hash`
- `emotion`
- `keywords`
- `summary`
- `created_at`

This separation keeps raw journal content and model-derived insights distinct.

---

## How would you scale this to 100k users?

To scale this system to 100k users, I would make the following changes.

### 1. Replace SQLite with PostgreSQL

SQLite is suitable for local development and small workloads, but not for high concurrency.  
For 100k users, PostgreSQL would be a better choice due to:

- better concurrent write support
- indexing support
- better production reliability
- stronger backup and replication options

### 2. Separate API and analysis workloads

Currently, analysis happens synchronously during the API request.  
At scale, I would split this into:

- API service for storing journal entries and serving reads
- background worker for LLM analysis

This prevents LLM latency from slowing down user-facing requests.

### 3. Add a queue

When a user requests analysis:

- save the entry immediately
- push an analysis job to a queue
- process jobs asynchronously

Possible tools:

- Redis + RQ or Celery
- RabbitMQ
- managed queue services

### 4. Add caching and precomputation

Frequently requested insights could be precomputed and stored rather than recalculated on every request.

### 5. Horizontal scaling

Deploy multiple backend instances behind a load balancer so requests can be distributed across servers.

### 6. Observability

At 100k users, monitoring becomes necessary:

- request latency
- LLM failures
- queue backlog
- database performance
- error rates

---

## How would you reduce LLM cost?

### 1. Cache repeated analysis

If the same text has already been analyzed, reuse the saved result instead of calling the LLM again.

### 2. Analyze only when necessary

Instead of auto-analyzing everything, only analyze:

- when the user clicks **Analyze**
- when text changes
- when no prior cached result exists

### 3. Use a strict output schema

The prompt only asks for:

- one emotion
- a few keywords
- one short summary

This keeps token usage small.

### 4. Use smaller or cheaper models where acceptable

For simple emotion classification and summarization, a smaller model may be enough.

### 5. Batch or debounce repeated requests

If users repeatedly click **Analyze** on the same entry, prevent duplicate LLM calls.

### 6. Use fallback logic for trivial cases

Very short or duplicate entries can use cached or lightweight logic before calling a full model.

---

## How would you cache repeated analysis?

The current implementation already does this using text hashing.

### Current caching flow

1. Normalize the journal text
   - trim whitespace
   - lowercase
   - collapse repeated spaces
2. Generate a SHA-256 hash
3. Check if an analysis already exists for that `text_hash`
4. If found:
   - return cached result
   - attach that cached result to the current journal entry if needed
5. If not found:
   - call the LLM
   - store the result
   - reuse it in future requests

### Why this works

It avoids repeated model calls for identical text and reduces latency and cost.

### Future improvement

Use Redis as an additional fast cache layer in front of the database.

---

## How would you protect sensitive journal data?

Journal data is private and emotionally sensitive, so security matters.

### 1. Encrypt data in transit

All communication should happen over HTTPS.

### 2. Encrypt data at rest

Stored journal text and backups should be encrypted.

### 3. Avoid logging raw journal text

Production logs should not contain sensitive user journal content.

### 4. Add authentication and authorization

Users should only be able to access their own entries and insights.

### 5. Protect secrets

API keys and credentials should be stored in environment variables or secret managers, never hardcoded in source control.

### 6. Minimize data exposure to the LLM

Only send the necessary journal text to the model.  
Do not send unnecessary metadata.

### 7. Add deletion and retention controls

Users should be able to delete their journal history, and the system should define retention rules.

### 8. Audit access

Sensitive data access should be traceable in production systems.

---

## Additional Improvements

### Rate limiting

Add per-user or per-IP rate limiting to prevent abuse of the analysis endpoint.

### Docker support

Containerize frontend and backend for reproducible local and deployment setups.

### Streaming support

If needed, LLM output could be streamed to the UI for better responsiveness.

### Model versioning

Store model name or version with the analysis result so changes can be tracked over time.

---

## Final Notes

This architecture was intentionally kept simple for the assignment:

- clear API structure
- real LLM integration
- persistent storage
- minimal frontend
- caching support

The system is production-extendable while still being small enough to implement and demonstrate quickly.