#!/bin/bash

pip install --upgrade poetry

poetry lock --no-update

echo "Lock file has been regenerated"
