import os

# Configuration
USER_BOT_TOKEN = "8496050580:AAHwP947Ydst-dI35Amirfumq87-yfCfn9Q"
ADMIN_BOT_TOKEN = "8507599807:AAEvrYW3CtmUUiG3jFFXunzH_FajdEXEIMU"
ADMIN_ID = 6787688428

# Web App URL
# Prioritize env var, default to localhost for local dev, but should be set in production
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://chagpt-free.onrender.com")

# Database
DATABASE_URL = "sqlite:///service_bot.db"
