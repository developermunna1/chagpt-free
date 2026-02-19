import os

# Configuration
# Attempt to read from environment variables, fallback to hardcoded (for local dev if .env not set)
# But strictly speaking, for Render, we want to use the Env Vars if provided.
USER_BOT_TOKEN = os.getenv("USER_BOT_TOKEN", "8496050580:AAHwP947Ydst-dI35Amirfumq87-yfCfn9Q")
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN", "8507599807:AAEvrYW3CtmUUiG3jFFXunzH_FajdEXEIMU")
ADMIN_ID = os.getenv("ADMIN_ID", "6787688428")

# Web App URL
# Prioritize env var, default to localhost for local dev, but should be set in production
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://chagpt-free.onrender.com")

# Database
DATABASE_URL = "sqlite:///service_bot.db"
