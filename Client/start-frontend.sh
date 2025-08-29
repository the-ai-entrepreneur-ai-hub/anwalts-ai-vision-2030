#!/bin/bash
echo "Starting AnwaltsAI Frontend..."

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    echo "Starting HTTP server on http://localhost:3000"
    python3 -m http.server 3000
elif command -v python &> /dev/null; then
    echo "Starting HTTP server on http://localhost:3000"
    python -m http.server 3000
else
    echo "Error: Python not found. Please install Python first."
    exit 1
fi