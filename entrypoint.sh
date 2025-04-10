#!/bin/bash

DEFAULT_PORT=8000

APP_PORT=${PORT:-$DEFAULT_PORT}

echo "Starting application on port: $APP_PORT"

exec uvicorn app.main:app --host 0.0.0.0 --port "$APP_PORT"
