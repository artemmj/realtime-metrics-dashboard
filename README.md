# Realtime Metrics Dashboard

Демонстрационный real-time дашборд на синтетических данных, реализующий эталонную микросервисную архитектуру с FastAPI, Celery, WebSocket и Vue.js для отработки практик построения масштабируемых наблюдаемых систем.

## 🛠 Tech Stack

- **Backend:** Python 3.13, FastAPI, SQLAlchemy 2.0 (Async), Pydantic V2
- **Frontend:** Vue.js (SPA)
- **Task Queue:** Celery + Redis
- **Database:** PostgreSQL 18 + Alembic
- **Infrastructure:** Docker Compose, Nginx (Reverse Proxy)
- **Package Manager:** uv

## 🏗 Project Structure

```text
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── main.py              # Entry point + router registration
│   ├── pyproject.toml
│   ├── src/
│   │   ├── auth_dependency.py
│   │   ├── celery_config.py
│   │   ├── db_dependency.py
│   │   ├── handlers/auth.py
│   │   ├── managers/user.py
│   │   ├── migrations/
│   │   ├── models/          # SQLAlchemy models & mixins
│   │   ├── redis_dependency.py
│   │   ├── routes/          # APIRouter endpoints (/v1/...)
│   │   ├── schemas/         # Pydantic validation models
│   │   ├── services/        # Business logic layer
│   │   ├── settings.py
│   │   └── tasks/           # Celery background jobs
│   ├── start.sh
│   └── uv.lock
├── frontend/                # Vue.js SPA (placeholder)
├── nginx/
│   └── nginx.conf           # Reverse proxy with /api/ prefix stripping
└── docker-compose.yml
```

🚀 Quick Start

Prerequisites
```
Docker & Docker Compose
uv (for local backend development outside Docker)
```
Run with Docker

```bash
# Copy environment variables
cp .env.example .env

# Build and start all services
docker compose up -d --build
```

Services will be available at:

Swagger UI: http://localhost/api/docs
ReDoc: http://localhost/api/redoc
Nginx Health: http://localhost/nginx-health
PostgreSQL: localhost:5432 (internal network only)

Local Development (Backend Only)

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn main:app --reload --port 8080
```
