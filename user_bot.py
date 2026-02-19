import logging
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from config import USER_BOT_TOKEN, WEB_APP_URL, ADMIN_ID
from database import get_db_connection

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def post_init(application: ApplicationBuilder):
    try:
        if ADMIN_ID:
            await application.bot.send_message(chat_id=ADMIN_ID, text="🚀 User Bot has launched with Web App UI!")
    except Exception as e:
        logging.error(f"Failed to send startup message: {e}")

async def register_user(user_id, username, first_name):
    conn = get_db_connection()
    try:
        conn.execute('INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)', 
                     (user_id, username, first_name))
        conn.commit()
    except Exception as e:
        logging.error(f"Error registering user: {e}")
    finally:
        conn.close()

async def check_membership(user_id, context):
    conn = get_db_connection()
    try:
        channels = conn.execute('SELECT * FROM channels').fetchall()
    except Exception as e:
        logging.error(f"Database error checking channels: {e}")
        return []
    finally:
        conn.close()

    missing_channels = []
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=ch['chat_id'], user_id=user_id)
            if member.status in ['left', 'kicked', 'restricted']:
                missing_channels.append(ch)
        except Exception as e:
            # Assume strict
            missing_channels.append(ch)
    
    return missing_channels

async def show_join_channels(update, context, missing_channels):
    keyboard = []
    for ch in missing_channels:
        btn_text = "📢 Join Channel"
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
    username = update.effective_user.username
    first_name = update.effective_user.first_name

    # Register user for broadcasts
    await register_user(user_id, username, first_name)
    
    # Check membership BEFORE showing content
    try:
        missing = await check_membership(user_id, context)
        if missing:
            await show_join_channels(update, context, missing)
            return
    except Exception as e:
        logging.error(f"Membership check failed: {e}")
        pass

    welcome_text = (
        f"🌟 Welcome, {first_name}! 🌟\n\n"
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
        else:
            await query.message.delete()
            # Recursively call start to show the menu
            await start(update, context)

if __name__ == '__main__':
    if not USER_BOT_TOKEN:
        print("Error: USER_BOT_TOKEN not found in environment.")
        exit(1)
        
    application = ApplicationBuilder().token(USER_BOT_TOKEN).post_init(post_init).build()
    
    start_handler = CommandHandler('start', start)
    btn_handler = CallbackQueryHandler(btn_handler)

    application.add_handler(start_handler)
    application.add_handler(btn_handler)
    
    print("User Bot is running...")
    application.run_polling()
