FROM python:3.11-slim

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VERSION=1.3.1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY poetry.lock pyproject.toml /app/

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install "poetry==$POETRY_VERSION"

# Add a fallback approach if the first attempt fails
RUN poetry config virtualenvs.create false \
    && (poetry install --only main --no-interaction --no-ansi || \
        (rm -f poetry.lock && poetry lock && poetry install --only main --no-interaction --no-ansi))

COPY . /app/

CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT