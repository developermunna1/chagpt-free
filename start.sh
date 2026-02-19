#!/bin/bash

# Initialize database
python database.py

# Start User Bot in background
python user_bot.py &

# Start Admin Bot in background
python admin_bot.py &

# Start Flask App (Blocking)
gunicorn app:app --bind 0.0.0.0:$PORT
