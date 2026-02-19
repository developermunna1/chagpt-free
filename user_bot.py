import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from config import USER_BOT_TOKEN, ADMIN_ID
from database import get_db_connection

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def post_init(application: ApplicationBuilder):
    try:
        if ADMIN_ID:
            await application.bot.send_message(chat_id=ADMIN_ID, text="🚀 User Bot has started with Native UI!")
    except Exception as e:
        logging.error(f"Failed to send startup message: {e}")

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
    
    keyboard.append([InlineKeyboardButton("✅ I have Joined", callback_data="check_joined")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg = "⛔ **Access Denied**\n\nPlease join our channels to use this bot."
    if update.callback_query:
        await update.callback_query.edit_message_text(msg, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, reply_markup=reply_markup, parse_mode='Markdown')

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
    except:
        pass

    user_name = update.effective_user.first_name
    text = (
        f"👋 **Hello, {user_name}!**\n\n"
        "Welcome to our **Premium Service Store**.\n"
        "Choose an option below to get started:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🛒 Buy Services", callback_data='menu_services')], # Changed from Web App to Callback
        [InlineKeyboardButton("👤 My Profile", callback_data='menu_profile'),
         InlineKeyboardButton("📞 Support", callback_data='menu_support')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        # If called from back button
        try:
            await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
        except:
            await update.callback_query.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup, parse_mode='Markdown')

async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    data = query.data
    
    if data == "check_joined":
        missing = await check_membership(user_id, context)
        if missing:
            await query.answer("❌ You haven't joined all channels!", show_alert=True)
        else:
            await query.message.delete()
            await start(update, context) # Show main menu
            
    elif data == "menu_main_menu":
        await start(update, context)

    elif data == "menu_services":
        conn = get_db_connection()
        services = conn.execute('SELECT * FROM services').fetchall()
        conn.close()
        
        if not services:
            await query.edit_message_text(
                "🛒 **Services**\n\nNo services available at the moment.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='menu_main_menu')]]),
                parse_mode='Markdown'
            )
            return

        keyboard = []
        for s in services:
            # Pass Service ID in callback data
            keyboard.append([InlineKeyboardButton(f"{s['name']} - ${s['price']}", callback_data=f"svc_{s['id']}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🛒 **Select a Service:**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    elif data == "menu_profile":
        text = (
            f"👤 **User Profile**\n\n"
            f"ID: `{user_id}`\n"
            f"Name: {query.from_user.full_name}\n\n"
            "Your order history will appear here."
        )
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='menu_main_menu')]])
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    elif data == "menu_support":
        text = (
            "📞 **Support**\n\n"
            "If you need help, contact our admin:\n"
            "@YourAdminUsername (Replace this)"
        )
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='menu_main_menu')]])
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    elif data.startswith("svc_"):
        # Handle Service Selection
        service_id = data.split("_")[1]
        
        conn = get_db_connection()
        service = conn.execute('SELECT * FROM services WHERE id = ?', (service_id,)).fetchone()
        conn.close()
        
        if not service:
            await query.answer("Service not found", show_alert=True)
            return
            
        text = (
            f"📦 **Order Summary**\n\n"
            f"**Service:** {service['name']}\n"
            f"**Price:** ${service['price']}\n"
            f"**Description:** {service['description']}\n\n"
            "Do you want to confirm this order?"
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirm Order", callback_data=f"confirm_{service_id}")],
            [InlineKeyboardButton("🔙 Cancel", callback_data='menu_services')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    elif data.startswith("confirm_"):
        service_id = data.split("_")[1]
        
        conn = get_db_connection()
        conn.execute('INSERT INTO orders (user_id, service_id, status) VALUES (?, ?, ?)', (user_id, service_id, 'pending'))
        conn.commit()
        conn.close()
        
        text = (
            "✅ **Order Placed Successfully!**\n\n"
            "Our team will process it shortly.\n"
            "You can check status in your Profile."
        )
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='menu_main_menu')]])
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')


if __name__ == '__main__':
    if not USER_BOT_TOKEN:
        print("Error: USER_BOT_TOKEN not found.")
        exit(1)
        
    application = ApplicationBuilder().token(USER_BOT_TOKEN).post_init(post_init).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(main_handler))
    
    print("User Bot is running...")
    application.run_polling()
