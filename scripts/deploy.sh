#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: Docker CLI is not installed or not in PATH."
  echo "Install Docker Desktop (macOS/Windows) or Docker Engine (Linux), then retry."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Error: Docker Compose v2 is required (docker compose ...)."
  exit 1
fi

if [[ ! -f .env ]]; then
  cat <<'ENV_HELP'
Error: .env file not found in repository root.
Create one with at least:
  GROQ_API_KEY=your_groq_api_key
Optional:
  BACKEND_URL=http://backend:8000
  CORS_ORIGINS=http://localhost:3000
ENV_HELP
  exit 1
fi

echo "Building and starting services..."
docker compose up -d --build

echo "Deployment completed."
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
