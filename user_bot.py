import logging
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from config import USER_BOT_TOKEN, WEB_APP_URL
from database import get_db_connection

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def check_membership(user_id, context):
    conn = get_db_connection()
    channels = conn.execute('SELECT * FROM channels').fetchall()
    conn.close()

    missing_channels = []
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=ch['chat_id'], user_id=user_id)
            if member.status in ['left', 'kicked', 'restricted']:
                missing_channels.append(ch)
        except Exception as e:
            logging.error(f"Error checking channel {ch['chat_id']}: {e}")
            # If bot can't check (e.g. not admin), we might want to skip or assume joined. 
            # For strictness, we assume missing if we can't verify, or you might choose to ignore.
            # Here we'll treat error as missing to force admin to fix permission.
            missing_channels.append(ch)
    
    return missing_channels

async def show_join_channels(update, context, missing_channels):
    keyboard = []
    for ch in missing_channels:
        # We can't easily get channel name without an API call that might fail if not admin
        # So we use "Join Channel" or trying to parse link
        btn_text = f"📢 Join Channel" 
        keyboard.append([InlineKeyboardButton(btn_text, url=ch['invite_link'])])
    
    keyboard.append([InlineKeyboardButton("✅ I Joined", callback_data="check_joined")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg_text = "⛔ **Access Denied**\n\nYou must join our official channels to use this bot."
    
    if update.callback_query:
        await update.callback_query.edit_message_text(msg_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg_text, reply_markup=reply_markup, parse_mode='Markdown')

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
    application = ApplicationBuilder().token(USER_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    btn_handler = CallbackQueryHandler(btn_handler)

    application.add_handler(start_handler)
    application.add_handler(btn_handler)
    
    print("User Bot is running...")
    application.run_polling()
