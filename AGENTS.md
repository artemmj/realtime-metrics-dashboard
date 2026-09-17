# Kilo Agents Configuration

This file contains commands and configurations for working with Kilo AI agents in this project.

## Development Commands

### Backend
```bash
# Run backend server locally
cd backend
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8080

# Run celery worker
cd backend
uv run celery -A src.celery_app worker --loglevel=info

# Run celery beat scheduler
cd backend
uv run celery -A src.celery_app beat --loglevel=info

# Run database migrations
cd backend
uv run alembic upgrade head

# Create new migration
cd backend
uv run alembic revision --autogenerate -m "description"

# Run tests
cd backend
uv run pytest

# Lint code
cd backend
uv run ruff check . --fix

# Type checking
cd backend
uv run pyright
```

### Frontend
```bash
# Run development server
cd frontend
npm run dev

# Build for production
cd frontend
npm run build

# Preview build
cd frontend
npm run preview

# Install dependencies
cd frontend
npm install
```

### Docker
```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f

# Rebuild containers
docker compose up -d --build

# Check service status
docker compose ps

# Execute command in running container
docker compose exec app bash

# View backend logs only
docker compose logs app -f

# View database logs only
docker compose logs db -f
```

### Project-wide
```bash
# Check Git status
git status

# Run project validation (if available)
make validate

# Run security scan
make security-scan
```

## Agent Configuration

The following commands are recognized by Kilo agents for this project:

### Testing and Validation
- `npm test` - Run frontend tests
- `uv run pytest` - Run backend tests
- `docker compose up -d --build` - Rebuild and start services
- `docker compose logs -f` - Follow container logs
- `uv run ruff check . --fix` - Lint Python code

### Database Operations
- `uv run alembic upgrade head` - Apply database migrations
- `docker compose exec db psql -U postgres` - Access PostgreSQL console
- `docker compose exec redis redis-cli` - Access Redis CLI

### Development Server Commands
- `cd backend && uv run uvicorn main:app --reload` - Start backend dev server
- `cd frontend && npm run dev` - Start frontend dev server
- `docker compose up -d` - Start all services in Docker

## Common Tasks for Agents

When working with this project, agents should:

1. **Before making changes**: Check if there are any running tests or services that might be affected
2. **After making code changes**: Run appropriate linting commands (`ruff check . --fix` for backend)
3. **Database schema changes**: Always create new migration with `alembic revision --autogenerate`
4. **Containerized development**: Use Docker commands for full-stack testing
5. **API testing**: Use the FastAPI docs at http://localhost/api/docs

## Environment Variables

Key environment variables for development:

```bash
# Backend (.env file in backend/)
SECRET_KEY=your-secret-key-here
POSTGRES_HOST=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## Health Checks

- Backend API: http://localhost/api/health
- Nginx: http://localhost/nginx-health
- PostgreSQL: `pg_isready -U postgres`
- Redis: `redis-cli ping`

## Monitoring Commands

```bash
# View resource usage
docker stats

# Check service health
docker compose ps --services --filter "status=running"

# View container logs
docker compose logs --tail=100

# Check network connectivity between containers
docker compose exec app ping db
```

## Backup and Recovery

```bash
# Backup database
docker compose exec db pg_dumpall -U postgres > backup.sql

# Backup Redis data
docker compose exec redis redis-cli save

# Restore database
cat backup.sql | docker compose exec -T db psql -U postgres

# Check data volume size
docker system df
```

## Security Commands

```bash
# Scan for vulnerabilities
docker scan <image_name>

# Check for secrets in code
# (install and configure appropriate tools)

# Audit dependencies
cd backend && uv audit
cd frontend && npm audit
```

## Performance Testing

```bash
# Monitor container CPU/memory
docker stats backend-app celery_worker db redis

# Test API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost/api/v1/metrics/

# Monitor WebSocket connections
# (check Redis PUBSUB CHANNELS)
docker compose exec redis redis-cli PUBSUB CHANNELS
```

This file helps Kilo agents understand the project structure and available commands for development, testing, and deployment.