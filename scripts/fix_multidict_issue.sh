#!/bin/bash

echo "Attempting to fix multidict dependency issue..."

pip install --upgrade poetry

poetry add multidict@">=5.0.0,<7.0.0"

poetry lock

if poetry check; then
    echo "Dependencies resolved successfully!"
else
    echo "Issue persists. Trying alternative approach..."
    
    poetry remove multidict
    poetry lock --no-update
    poetry add multidict@"^6.0.0"
    
    if poetry check; then
        echo "Dependencies resolved successfully with alternative approach!"
    else
        echo "Dependency issues still exist. Manual intervention required."
        echo "Check the output of: poetry show --tree"
    fi
fi
