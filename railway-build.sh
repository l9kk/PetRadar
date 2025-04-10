#!/bin/bash
set -e

# Install Poetry
pip install poetry

# Configure Poetry to not create a virtual environment
poetry config virtualenvs.create false

# Install dependencies
poetry install --without dev 

# Run migrations
alembic upgrade head

echo "Railway build completed successfully"