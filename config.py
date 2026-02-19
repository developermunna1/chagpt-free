import os

# Configuration
# Attempt to read from environment variables.
# CRITICAL: These MUST be set in Render Environment Variables.
USER_BOT_TOKEN = os.getenv("USER_BOT_TOKEN")
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# Web App URL
# Prioritize env var, default to localhost for local dev, but should be set in production
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://chagpt-free.onrender.com")

# Database
DATABASE_URL = "sqlite:///service_bot.db"
