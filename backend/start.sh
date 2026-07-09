#!/bin/sh
set -e

ENV_FILE="${ENV_FILE:-./.env}"

if [ -f "${ENV_FILE}" ]; then
    set -a
    source "${ENV_FILE}"
    set +a
fi

echo "(start.sh) Running database migrations..."
if ! uv run -m src.scripts.safe_alembic_upgrade; then
    echo "(start.sh) Migrations failed! Please try again..." >&2
fi

echo "(start.sh) 🚀 Starting FastAPI..."
exec uv run uvicorn main:app --host 0.0.0.0 --port 8080 --workers 2
