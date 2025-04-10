#!/bin/bash
set -e

echo "Current directory: $(pwd)"
echo "Files in directory: $(ls -la)"
echo "Environment variables:"
echo "PORT=$PORT"
echo "DATABASE_URL=${DATABASE_URL//:\/\//:\/\/***:***@}"

if [ -z "$PORT" ]; then
    PORT_NUM=8000
    echo "PORT not set, defaulting to $PORT_NUM"
else
    PORT_NUM=$PORT
    echo "Using PORT: $PORT_NUM"
fi

echo "Running database migrations..."
alembic upgrade head || echo "Warning: Database migrations failed, but continuing startup"

echo "Starting application on port $PORT_NUM..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT_NUM"
