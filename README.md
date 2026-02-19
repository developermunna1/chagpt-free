# Service Buying Bot - Setup & Deployment Guide

## 🚀 Quick Start
1.  **Initialize Database**: `python database.py`
2.  **Run Locally (Web App)**: `python app.py`
3.  **Run Bots**: `python user_bot.py` and `python admin_bot.py` (in separate terminals)

## 💎 VIP UI
- Access the web interface at `http://localhost:5000` (locally) or your Render URL.
- The UI features a premium dark/gold theme with smooth animations.

## ☁️ Deploy to Render
1.  Push this code to a new GitHub repository.
2.  Go to [Render Dashboard](https://dashboard.render.com/).
3.  Click **New +** -> **Web Service**.
4.  Connect your GitHub repo.
5.  Render should automatically detect `render.yaml` or use the `Dockerfile`.
    - **Build Command**: `pip install -r requirements.txt`
    - **Start Command**: `./start.sh`
6.  Add Environment Variables if needed (e.g., specific secrets), though `config.py` currently holds the tokens directly (consider moving to env vars for security in production).

## 🤖 Bot Commands
- **Admin Bot**:
    - `/start`: Check admin access.
    - `/add_service <name> <price> <desc>`: Add a new service.
    - `/orders`: View recent orders.
- **User Bot**:
    - `/start`: Receive the Welcome message with the Web App link.

## 📂 Project Structure
- `app.py`: Flask Web App
- `user_bot.py`: User Telegram Bot
- `admin_bot.py`: Admin Telegram Bot
- `database.py`: Database setup
- `templates/`: HTML files
- `static/`: CSS/JS files
- `Dockerfile` & `render.yaml`: Deployment config
