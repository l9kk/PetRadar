#!/bin/bash

echo "Regenerating poetry.lock file..."

# Remove the old lock file
rm -f poetry.lock

# Generate a new lock file
poetry lock

echo "Lock file regenerated successfully!"
