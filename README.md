# 📊 Real-Time Metrics Dashboard

Демонстрационное веб-приложение для мониторинга системных метрик в реальном времени. Состоит из трёх компонентов: **Vue 3 SPA** (фронтенд), **FastAPI** (бэкенд) и **Nginx** (прокси-сервер). Метрики генерируются асинхронно через Celery, сохраняются в PostgreSQL и транслируются клиентам через WebSocket с использованием Redis Pub/Sub.

## 🏗️ Архитектура

```mermaid
graph TD
    Browser[Browser - Vue 3 SPA]
    Nginx[Nginx - proxy, port 80]
    FastAPI[FastAPI - backend, port 8080]
    PostgreSQL[(PostgreSQL - metrics + users)]
    Redis[(Redis - broker + cache + pub/sub)]
    CeleryBeat[Celery Beat - scheduler]
    CeleryWorker[Celery Worker - metrics generator]

    Browser <-->|HTTP + WebSocket| Nginx
    Nginx <-->|proxy /api and /ws| FastAPI
    FastAPI -->|CRUD| PostgreSQL
    FastAPI <-->|JWT sessions + pub/sub| Redis
    CeleryBeat -->|send tasks| Redis
    CeleryWorker -->|consume tasks| Redis
    CeleryWorker -->|save metrics| PostgreSQL
    CeleryWorker -->|publish to channel| Redis
```

## 🔄 Поток данных метрик

```mermaid
sequenceDiagram
    participant Beat as Celery Beat
    participant Queue as Redis Queue
    participant Worker as Celery Worker
    participant DB as PostgreSQL
    participant PubSub as Redis Pub/Sub
    participant API as FastAPI WebSocket
    participant UI as Vue 3 Dashboard

    loop Every 2 seconds
        Beat->>Queue: send "generate_metrics" task
    end

    Queue->>Worker: consume task
    Worker->>Worker: generate random metric
    Worker->>DB: INSERT into metrics table
    Worker->>PubSub: PUBLISH "metrics:new"
    PubSub->>API: message to subscriber
    API->>UI: WebSocket message
    UI->>UI: update dashboard
```

**По шагам:**
1. **Celery Beat** по расписанию (каждые 2 секунды) отправляет задачу `generate_metrics` в очередь Redis.
2. **Celery Worker** забирает задачу, генерирует случайную метрику (`cpu_usage`, `memory_usage`, `active_users`, `requests_per_sec`).
3. Метрика сохраняется в **PostgreSQL** через SQLAlchemy.
4. После сохранения публикуется сообщение в **Redis Pub/Sub** (канал `metrics:new`).
5. **FastAPI WebSocket**-эндпоинт подписан на этот канал и рассылает новые метрики всем подключённым клиентам.
6. **Vue 3 фронтенд** получает метрику, обновляет сводку и графики в реальном времени.

## 🔐 Поток аутентификации

```mermaid
sequenceDiagram
    participant Browser as Browser
    participant Nginx as Nginx
    participant API as FastAPI
    participant DB as PostgreSQL
    participant Redis as Redis

    Note over Browser,Redis: Registration
    Browser->>Nginx: POST /api/v1/auth/register
    Nginx->>API: proxy request
    API->>DB: INSERT into users
    API->>Browser: 201 + user data

    Note over Browser,Redis: Login
    Browser->>Nginx: POST /api/v1/auth/login
    Nginx->>API: proxy request
    API->>DB: SELECT user by email
    API->>API: verify password (bcrypt)
    API->>Redis: save session (TTL 24h)
    API->>Browser: 200 + JWT token
    Browser->>Browser: save token to localStorage

    Note over Browser,Redis: Protected request
    Browser->>Nginx: GET /api/v1/metrics/
    Nginx->>API: proxy + Authorization header
    API->>Redis: check session
    Redis->>API: session active
    API->>DB: SELECT metrics
    API->>Browser: 200 + metrics array

    Note over Browser,Redis: WebSocket
    Browser->>Nginx: WS /api/v1/metrics/ws
    Nginx->>API: upgrade to WebSocket
    API->>Redis: check session
    API->>Redis: SUBSCRIBE "metrics:new"
    loop New metrics
        Redis->>API: message from Pub/Sub
        API->>Browser: JSON metric
    end
```

### Дополнительно: REST API
Клиент может запросить историю метрик через `GET /api/v1/metrics/?limit=100&offset=0` — данные читаются напрямую из PostgreSQL.

## 🚀 Быстрый старт

### Предварительные требования
- [Docker](https://docs.docker.com/get-docker/) и Docker Compose
- [Node.js](https://nodejs.org/) 18+ (только для локальной разработки фронтенда)

### Запуск всего стека

```bash
# 1. Клонировать репозиторий
git clone <repo-url> metrics-dashboard
cd metrics-dashboard
```

# 2. Создать .env файл с переменными окружения (опционально, или скопировать из .env.example)
```bash
cat > .env << EOF
SECRET_KEY=your-secret-key-here
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
POSTGRES_HOST=db
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
EOF
```

# 3. Запустить все сервисы
```bash
docker compose up -d
```

# 4. Проверить состояние
```bash
docker compose ps
```

После запуска:

- Фронтенд + API: http://localhost (порт 80)
- API напрямую (минуя Nginx): http://localhost:8080
- PostgreSQL: localhost:5432
- Redis: доступен внутри Docker-сети
