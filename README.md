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
├── package.json
├── README.md
└── ARCHITECTURE.md