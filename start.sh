#!/bin/bash

# Force unbuffered output
export PYTHONUNBUFFERED=1

echo "Starting Bots (User & Admin)..."
python main.py &

echo "Starting Web App on 0.0.0.0:$PORT..."
# Run Gunicorn in foreground
gunicorn app:app --bind 0.0.0.0:$PORT --log-level info
