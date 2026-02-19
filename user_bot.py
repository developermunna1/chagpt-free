import logging
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from config import USER_BOT_TOKEN, WEB_APP_URL, ADMIN_ID
from database import get_db_connection

# ... (logging setup)

async def post_init(application: ApplicationBuilder):
    try:
        await application.bot.send_message(chat_id=ADMIN_ID, text="🚀 User Bot has started and is running on Render!")
    except Exception as e:
        logging.error(f"Failed to send startup message: {e}")

# ... (rest of the file)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    missing = await check_membership(user_id, context)
    
    if missing:
        await show_join_channels(update, context, missing)
        return

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

async def btn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "check_joined":
        user_id = query.from_user.id
        missing = await check_membership(user_id, context)
        
        if missing:
            await query.answer("❌ You haven't joined all channels yet!", show_alert=True)
            # Optional: Refresh the list if it changed, currently just showing alert
        else:
            await query.message.delete()
            # Call start logic again or just send the menu
            await start(update, context)

if __name__ == '__main__':
    application = ApplicationBuilder().token(USER_BOT_TOKEN).post_init(post_init).build()
    
    start_handler = CommandHandler('start', start)
    btn_handler = CallbackQueryHandler(btn_handler)

    application.add_handler(start_handler)
    application.add_handler(btn_handler)
    
    print("User Bot is running...")
    application.run_polling()
