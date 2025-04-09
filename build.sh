#!/bin/bash
set -e

pip install poetry

poetry config virtualenvs.create false

poetry install --no-dev

echo "Build completed successfully"
