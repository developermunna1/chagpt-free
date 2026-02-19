#!/bin/bash

# Force unbuffered output
export PYTHONUNBUFFERED=1

echo "Initializing database..."
python database.py

echo "Starting User Bot..."
python user_bot.py &

echo "Starting Admin Bot..."
python admin_bot.py &

echo "Starting Web App on 0.0.0.0:$PORT..."
# Run Gunicorn in foreground. If this exits, the container exits/restarts.
gunicorn app:app --bind 0.0.0.0:$PORT --log-level info
