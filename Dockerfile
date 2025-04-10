FROM python:3.11.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml poetry.lock* ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install poetry==1.7.1 && \
    poetry config virtualenvs.create false && \
    poetry config experimental.system-git-client true && \
    # Force a specific version of multidict to avoid the yanked 6.3.2 version
    pip install multidict==6.0.4 && \
    poetry install --without dev --no-interaction

# Copy the rest of the application
COPY . .

# Run database migrations and start the application
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT