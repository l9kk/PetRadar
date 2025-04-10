#!/bin/bash
set -e

echo "Current directory: $(pwd)"
echo "Files in directory: $(ls -la)"
echo "Environment variables:"
echo "PORT=$PORT"
echo "DATABASE_URL=${DATABASE_URL//:\/\//:\/\/***:***@}"

echo "Running database migrations..."
alembic upgrade head || echo "Warning: Database migrations failed, but continuing startup"

if [ -z "$PORT" ]; then
    echo "PORT not set, defaulting to 8000"
    export PORT=8000
fi

echo "Starting application on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
