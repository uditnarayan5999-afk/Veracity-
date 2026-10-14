#!/bin/bash

# Change to the backend directory relative to this script
cd "$(dirname "$0")"

# Activate the virtual environment
source venv/bin/activate

# Run Uvicorn directly
exec uvicorn main:app --host 0.0.0.0 --port 8000
