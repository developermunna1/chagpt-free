import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from config import USER_BOT_TOKEN, ADMIN_ID
from database import get_db_connection

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def post_init(application: ApplicationBuilder):
    try:
        if ADMIN_ID:
            await application.bot.send_message(chat_id=ADMIN_ID, text="🚀 User Bot launched with Referral System!")
    except: pass

async def register_user(user_id, username, first_name, referrer_id=None):
    conn = get_db_connection()
    try:
        # Check if user exists
        exists = conn.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,)).fetchone()
        if not exists:
            conn.execute('INSERT INTO users (user_id, username, first_name, referred_by) VALUES (?, ?, ?, ?)', 
                         (user_id, username, first_name, referrer_id))
            conn.commit()
            
            # Bonus logic for referrer could go here
            if referrer_id:
                # Notify referrer?
                pass
    except Exception as e:
        logging.error(f"Error registering: {e}")
    finally:
        conn.close()

async def check_membership(user_id, context):
    conn = get_db_connection()
    try:
        channels = conn.execute('SELECT * FROM channels').fetchall()
    except:
        return []
    finally:
        conn.close()

    missing_channels = []
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=ch['chat_id'], user_id=user_id)
            if member.status in ['left', 'kicked', 'restricted']:
                missing_channels.append(ch)
        except:
            missing_channels.append(ch)
    return missing_channels

async def show_join_channels(update, context, missing_channels):
    keyboard = []
    for ch in missing_channels:
        keyboard.append([InlineKeyboardButton("📢 Join Channel", url=ch['invite_link'])])
    keyboard.append([InlineKeyboardButton("✅ I Joined", callback_data="check_joined")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = "⛔ **Access Denied**\n\nPlease join our channels to control this bot."
    
    if update.callback_query:
        await update.callback_query.edit_message_text(msg, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, reply_markup=reply_markup, parse_mode='Markdown')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name

    # Handle Referral
    args = context.args
    referrer_id = None
    if args and args[0].isdigit():
        potential_referrer = int(args[0])
        if potential_referrer != user_id:
            referrer_id = potential_referrer

    await register_user(user_id, username, first_name, referrer_id)
    
    try:
        missing = await check_membership(user_id, context)
        if missing:
            await show_join_channels(update, context, missing)
            return
    except: pass

    text = (
        f"👋 **Hello, {first_name}!** (v2.0)\n\n"
        "Welcome to your **Premium Dashboard**.\n"
        "Earn credits by referring friends or add funds to buy services!"
    )
    
    keyboard = [
        [InlineKeyboardButton("👤 My Profile", callback_data="show_profile"),
         InlineKeyboardButton("💰 Add Credits", callback_data="add_balance")],
        [InlineKeyboardButton("🔗 Refer & Earn", callback_data="referral_info")],
        [InlineKeyboardButton("🛍️ Services", callback_data="list_services")] # Keeping service list button
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup, parse_mode='Markdown')

async def btn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    if query.data == "check_joined":
        missing = await check_membership(user_id, context)
        if missing:
            await query.answer("❌ Join channels first!", show_alert=True)
        else:
            await query.message.delete()
            await start(update, context)

    elif query.data == "back_to_menu":
        await start(update, context)

    elif query.data == "show_profile":
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
        conn.close()
        balance = user['balance'] if user else 0.0
        
        text = (
            f"👤 **My Profile**\n\n"
            f"🆔 ID: `{user_id}`\n"
            f"👤 Name: {query.from_user.full_name}\n"
            f"💳 Credits: **{balance:.2f}**\n\n"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif query.data == "add_balance":
        text = (
            "💰 **Add Credits**\n\n"
            "Contact Admin to buy credits:\n"
            "👤 Admin: @YourAdminUsername\n\n"
            "**Accepted:**\n"
            "• Binance\n• Bkash\n• Nagad"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif query.data == "referral_info":
        bot_username = context.bot.username
        link = f"https://t.me/{bot_username}?start={user_id}"
        
        text = (
            "🔗 **Refer & Earn**\n\n"
            "Share your link and earn bonus credits!\n\n"
            f"Your Link:\n`{link}`\n\n"
            "Tap to copy!"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif query.data == "list_services":
        # Placeholder for service listing
        await query.answer("Service list coming in next update!", show_alert=True)

if __name__ == '__main__':
    if not USER_BOT_TOKEN: exit(1)
    application = ApplicationBuilder().token(USER_BOT_TOKEN).post_init(post_init).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(btn_handler))
    print("User Bot Running...")
    application.run_polling()
