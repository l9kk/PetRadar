#!/bin/bash
PORT=${PORT:-8000}

echo "Starting server on port: $PORT"

uvicorn app.main:app --host 0.0.0.0 --port $PORT
