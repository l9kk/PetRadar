#!/bin/bash

# Hardcoded port for now
uvicorn app.main:app --host 0.0.0.0 --port 8000uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
