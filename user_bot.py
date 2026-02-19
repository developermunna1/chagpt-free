import logging
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from config import USER_BOT_TOKEN, WEB_APP_URL

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    welcome_text = (
        f"🌟 Welcome, {user_first_name}! 🌟\n\n"
        "Unlock the VIP experience. Tap the button below to browse our exclusive services."
    )
    
    keyboard = [
        [InlineKeyboardButton("💎 Open VIP Store", web_app=WebAppInfo(url=WEB_APP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=welcome_text,
        reply_markup=reply_markup
    )

if __name__ == '__main__':
    application = ApplicationBuilder().token(USER_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    
    print("User Bot is running...")
    application.run_polling()
