# realtime-metrics-dashboard

Демонстрационный real-time дашборд на синтетических данных, реализующий эталонную микросервисную архитектуру с FastAPI, Celery, WebSocket и Vue.js для отработки практик построения масштабируемых наблюдаемых систем.

realtime-metrics-dashboard

## 🛠 Tech Stack

- **Backend:** Python 3.13, FastAPI, SQLAlchemy 2.0 (Async), Pydantic V2
- **Task Queue:** Celery + Redis
- **Database:** PostgreSQL 18 + Alembic
- **Infrastructure:** Docker Compose, Nginx (Reverse Proxy)
- **Package Manager:** uv

## 🏗 Project Structure

```text
├── README.md
├── backend
│   ├── Dockerfile
│   ├── README.md
│   ├── alembic.ini
│   ├── main.py
│   ├── pyproject.toml
│   ├── src
│   │   ├── auth_dependency.py
│   │   ├── celery_config.py
│   │   ├── db_dependency.py
│   │   ├── handlers
│   │   │   └── auth.py
│   │   ├── managers
│   │   │   └── user.py
│   │   ├── migrations/
│   │   ├── models
│   │   │   ├── base.py
│   │   │   ├── mixins.py
│   │   │   └── user.py
│   │   ├── redis_dependency.py
│   │   ├── routes
│   │   │   ├── auth.py
│   │   │   └── users.py
│   │   ├── schemas
│   │   │   └── user.py
│   │   ├── services
│   │   │   └── user.py
│   │   ├── settings.py
│   │   └── tasks
│   │       └── send_email.py
│   ├── start.sh
│   └── uv.lock
├── docker-compose.yml
└── nginx
    └── nginx.conf
```

🚀 Quick Start
Prerequisites

    Docker & Docker Compose
    uv (for local backend development outside Docker)

Run with Docker

```bash
# Copy environment variables
cp .env.example .env

# Build and start all services
docker compose up -d --build
```

Services will be available at:

- API: http://localhost/api/docs
- Nginx Health: http://localhost/nginx-health
- PostgreSQL: localhost:5432 (internal only via Nginx network)

Local Development (Backend Only)

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn main:app --reload --port 8080
```

⚙️ Key Features

- Async-first architecture – Non-blocking I/O for high concurrency
- Layered structure – Routes → Services → Managers → Models separation
- Celery integration – Background tasks (email, metrics aggregation)
- Nginx reverse proxy – Unified entry point, gzip, WebSocket support, SPA-ready
- Health checks – Built-in endpoints for all critical services
- Type-safe validation – Pydantic models with enum control & serialization
