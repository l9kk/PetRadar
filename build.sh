#!/bin/bash
set -e

# Install Poetry 2.1.2 (or your preferred version)
curl -sSL https://install.python-poetry.org | python3 - --version 2.1.2

# Add Poetry to PATH
export PATH="$HOME/.local/bin:$PATH"

# Configure Poetry to not create a virtual environment
poetry config virtualenvs.create false

# Install dependencies
poetry install --without dev

echo "Build completed successfully"
