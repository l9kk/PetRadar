#!/bin/bash
set -e

echo "Environment variables:"
echo "PORT=$PORT"
echo "DATABASE_URL=${DATABASE_URL//:\/\//:\/\/***:***@}"

echo "Running database migrations..."
alembic upgrade head || echo "Warning: Database migrations failed, but continuing startup"

echo "Starting application on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
