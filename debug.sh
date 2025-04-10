#!/bin/bash

echo "=== Railway Debug Script ==="
echo "Current date: $(date)"
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"
echo "Directory contents: $(ls -la)"
echo "Environment variables:"
env | grep -v -E 'PASSWORD|SECRET|TOKEN|KEY'
echo "Operating system: $(uname -a)"
echo "Network info:"
ip addr show || echo "ip command not available"
echo "Port availability:"
netstat -tulpn || ss -tulpn || echo "Network tools not available"

echo "Starting debug server..."
python debug.py
