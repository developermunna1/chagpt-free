#!/bin/bash

# Force unbuffered output
export PYTHONUNBUFFERED=1

# Initialize database
python database.py

# Start User Bot
echo "Starting User Bot..."
python -u user_bot.py &
USER_BOT_PID=$!

# Start Admin Bot
echo "Starting Admin Bot..."
python -u admin_bot.py &
ADMIN_BOT_PID=$!

# Start Flask App
echo "Starting Web App..."
gunicorn app:app --bind 0.0.0.0:$PORT &
WEB_APP_PID=$!

# Wait for any process to exit
wait -n

# Get exit code
EXIT_CODE=$?
echo "A process exited with code $EXIT_CODE. Shutting down..."
exit $EXIT_CODE
