FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN pip install uvicorn

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock README.md alembic.ini main.py start.sh ./
COPY src/ ./src/

RUN uv sync --frozen

RUN chmod +x ./start.sh
EXPOSE 8080
CMD ["./start.sh"]
