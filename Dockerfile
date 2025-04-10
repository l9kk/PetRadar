FROM python:3.11.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* ./

RUN pip install --upgrade pip && \
    pip install poetry==1.7.1 && \
    poetry config virtualenvs.create false && \
    poetry config experimental.system-git-client true && \
    pip install multidict==6.0.4 && \
    poetry install --without dev --no-interaction

COPY . .

CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT