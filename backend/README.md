# 📊 Real-Time Metrics Dashboard

Полноценное веб-приложение для мониторинга системных метрик в реальном времени. Состоит из трёх компонентов: **Vue 3 SPA** (фронтенд), **FastAPI** (бэкенд) и **Nginx** (прокси-сервер). Метрики генерируются асинхронно через Celery, сохраняются в PostgreSQL и транслируются клиентам через WebSocket с использованием Redis Pub/Sub.

## 🏗️ Архитектура

graph TD
    Browser["🖥️ Браузер<br/>(Vue 3 SPA)"]
    Nginx["🔀 Nginx<br/>(прокси, порт 80)"]
    FastAPI["⚡ FastAPI<br/>(бэкенд, порт 8080)"]
    PostgreSQL["🗄️ PostgreSQL<br/>(метрики + пользователи)"]
    Redis["📦 Redis<br/>(брокер Celery + кэш сессий + Pub/Sub)"]
    CeleryBeat["⏰ Celery Beat<br/>(планировщик задач)"]
    CeleryWorker["🔧 Celery Worker<br/>(генерация метрик)"]

    Browser <-->|"HTTP + WebSocket"| Nginx
    Nginx <-->|"проксирует /api/ и /ws"| FastAPI
    FastAPI -->|"CRUD"| PostgreSQL
    FastAPI <-->|"сессии JWT + Pub/Sub"| Redis
    CeleryBeat -->|"отправляет задачи"| Redis
    CeleryWorker -->|"забирает задачи"| Redis
    CeleryWorker -->|"сохраняет метрики"| PostgreSQL
    CeleryWorker -->|"публикует в канал"| Redis

## 🔄 Поток данных метрик

sequenceDiagram
    participant Beat as ⏰ Celery Beat
    participant Queue as 📦 Redis (очередь)
    participant Worker as 🔧 Celery Worker
    participant DB as 🗄️ PostgreSQL
    participant PubSub as 📢 Redis (Pub/Sub)
    participant API as ⚡ FastAPI WebSocket
    participant UI as 🖥️ Vue 3 Dashboard

    loop Каждые 2 секунды
        Beat->>Queue: отправить задачу "generate_metrics"
    end

    Queue->>Worker: забрать задачу
    Worker->>Worker: сгенерировать случайную метрику<br/>(cpu_usage / memory_usage /<br/>active_users / requests_per_sec)
    Worker->>DB: INSERT в таблицу metrics
    Worker->>PubSub: PUBLISH "metrics:new" { metric }
    PubSub->>API: сообщение подписчику
    API->>UI: WebSocket message (JSON)
    UI->>UI: обновить сводку и историю

    Note over UI,API: Клиент также может запросить<br/>историю через GET /api/v1/metrics/

**По шагам:**
1. **Celery Beat** по расписанию (каждые 2 секунды) отправляет задачу `generate_metrics` в очередь Redis.
2. **Celery Worker** забирает задачу, генерирует случайную метрику (`cpu_usage`, `memory_usage`, `active_users`, `requests_per_sec`).
3. Метрика сохраняется в **PostgreSQL** через SQLAlchemy.
4. После сохранения публикуется сообщение в **Redis Pub/Sub** (канал `metrics:new`).
5. **FastAPI WebSocket**-эндпоинт подписан на этот канал и рассылает новые метрики всем подключённым клиентам.
6. **Vue 3 фронтенд** получает метрику, обновляет сводку и графики в реальном времени.

## 🔐 Поток аутентификации

sequenceDiagram
    participant Browser as 🖥️ Браузер
    participant Nginx as 🔀 Nginx
    participant API as ⚡ FastAPI
    participant DB as 🗄️ PostgreSQL
    participant Redis as 📦 Redis

    Note over Browser,Redis: === Регистрация ===
    Browser->>Nginx: POST /api/v1/auth/register
    Nginx->>API: проксирует запрос
    API->>DB: INSERT в таблицу users
    API->>Browser: 201 + данные пользователя

    Note over Browser,Redis: === Вход ===
    Browser->>Nginx: POST /api/v1/auth/login
    Nginx->>API: проксирует запрос
    API->>DB: SELECT user по email
    API->>API: проверить пароль (bcrypt)
    API->>Redis: сохранить сессию (TTL 24ч)
    API->>Browser: 200 + JWT токен
    Browser->>Browser: сохранить токен в localStorage

    Note over Browser,Redis: === Защищённый запрос ===
    Browser->>Nginx: GET /api/v1/metrics/ (Authorization: JWT)
    Nginx->>API: проксирует запрос + заголовок
    API->>Redis: проверить сессию
    Redis->>API: сессия активна
    API->>DB: SELECT метрики
    API->>Browser: 200 + массив метрик

    Note over Browser,Redis: === WebSocket ===
    Browser->>Nginx: WS /api/v1/metrics/ws?token=JWT
    Nginx->>API: Upgrade до WebSocket
    API->>Redis: проверить сессию
    API->>Redis: SUBSCRIBE "metrics:new"
    loop Новые метрики
        Redis->>API: сообщение из Pub/Sub
        API->>Browser: JSON с метрикой
    end

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
