import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, filters, MessageHandler
from config import ADMIN_BOT_TOKEN, ADMIN_ID
from database import get_db_connection
import traceback

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Helper to check admin
def is_admin(user_id):
    try:
        return str(user_id) == str(ADMIN_ID)
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await context.bot.send_message(chat_id=user_id, text="⛔ Access Denied.")
        return

    keyboard = [
        [InlineKeyboardButton("🛍️ Services", callback_data='btn_services'),
         InlineKeyboardButton("📦 Orders", callback_data='btn_orders')],
        [InlineKeyboardButton("📢 Channels", callback_data='btn_channels')],
        [InlineKeyboardButton("🔄 Refresh", callback_data='btn_refresh')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "👑 **Admin Dashboard** 👑\n\n"
            "Welcome to your control panel.\n"
            "Select an action below:"
        ),
        reply_markup=reply_markup
    )
    # Note: Removed markdown parse_mode to be safe, or we can use it if we are careful. 
    # Let's keep it simple for now to avoid crash.

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.answer("⛔ Access Denied", show_alert=True)
        return

    await query.answer()
    data = query.data

    back_btn = [InlineKeyboardButton("🔙 Back to Dashboard", callback_data='btn_refresh')]

    if data == 'btn_refresh':
        keyboard = [
            [InlineKeyboardButton("🛍️ Services", callback_data='btn_services'),
             InlineKeyboardButton("📦 Orders", callback_data='btn_orders')],
            [InlineKeyboardButton("📢 Channels", callback_data='btn_channels')],
            [InlineKeyboardButton("🔄 Refresh", callback_data='btn_refresh')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.edit_message_text(
                text="👑 **Admin Dashboard** 👑\n\nWelcome to your control panel.\nSelect an action below:",
                reply_markup=reply_markup
            )
        except:
            pass # Message might be same

    elif data == 'btn_services':
        # List services
        conn = get_db_connection()
        services = conn.execute('SELECT * FROM services').fetchall()
        conn.close()

        text = "🛍️ **Manage Services**\n\n"
        if not services:
            text += "No services found.\n"
        else:
            for s in services:
                text += f"• {s['name']} - ${s['price']}\n  ID: {s['id']}\n\n"
        
        text += "To add a service, send command:\n`/add_service Name Price Description`"
        
        keyboard = [back_btn]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)

    elif data == 'btn_orders':
        conn = get_db_connection()
        # Fetch last 5 orders
        orders = conn.execute('SELECT * FROM orders ORDER BY timestamp DESC LIMIT 5').fetchall()
        conn.close()

        text = "📦 **Recent Orders**\n\n"
        if not orders:
            text += "No pending orders."
        else:
            for o in orders:
                text += f"🆔 Order #{o['id']}\n👤 User: {o['user_id']}\n🛠 Svc ID: {o['service_id']}\nscStatus: {o['status']}\n\n"
        
        keyboard = [back_btn]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)

    elif data == 'btn_channels':
        conn = get_db_connection()
        channels = conn.execute('SELECT * FROM channels').fetchall()
        conn.close()

        text = "📢 **Verification Channels**\n\n"
        if not channels:
            text += "No channels configured.\n"
        else:
            for ch in channels:
                text += f"ID: {ch['chat_id']}\nLink: {ch['invite_link']}\n\n"
        
        text += (
            "To ADD: `/add_channel <id> <link>`\n"
            "To DEL: `/del_channel <id>`"
        )
        
        keyboard = [back_btn]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)

# Keep command handlers for adding data as they require arguments
async def add_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Usage: /add_service <name> <price> <description>")
        return
    try:
        name, price, description = args[0], float(args[1]), " ".join(args[2:])
        conn = get_db_connection()
        conn.execute('INSERT INTO services (name, price, description) VALUES (?, ?, ?)', (name, price, description))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"✅ Service '{name}' added!")
    except Exception as e:
        await update.message.reply_text("❌ Error adding service.")

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    
    # Check if user sent arguments
    if not args:
        await update.message.reply_text(
            "📝 **How to Add a Channel:**\n\n"
            "Simply send:\n`/add_channel https://t.me/your_channel`\n"
            "OR\n`/add_channel @your_channel`\n\n"
            "⚠️ The bot MUST be an **Admin** in that channel!",
            parse_mode='Markdown'
        )
        return

    user_input = args[0]
    chat_id = None
    invite_link = user_input

    try:
        # Try to resolve username/link from input
        username = None
        if "t.me/" in user_input:
            # Extract username from link (e.g., https://t.me/username)
            parts = user_input.split('/')
            if parts[-1].startswith('+'):
                # Private invite link, cannot resolve ID easily without being in it
                await update.message.reply_text("⚠️ Private links (starting with +) usage:\n`/add_channel <id> <link>`", parse_mode='Markdown')
                return
            username = f"@{parts[-1]}"
        elif user_input.startswith("@"):
            username = user_input
        
        # If we found a username, fetch the chat info
        if username:
            try:
                chat = await context.bot.get_chat(username)
                chat_id = chat.id
                # Use the passed link or username as display
                invite_link = user_input
            except Exception as e:
                await update.message.reply_text(f"❌ Could not find channel {username}.\nMake sure the bot is an **Admin** there or the username is correct.")
                return
        else:
            # Maybe user provided ID first? (Old syntax support: ID Link)
            if len(args) >= 2:
                chat_id = args[0]
                invite_link = args[1]
            else:
                await update.message.reply_text("❌ Invalid format. Please use a public link or @username.")
                return

        # Save to DB
        conn = get_db_connection()
        # Check if exists
        curr = conn.execute('SELECT * FROM channels WHERE chat_id = ?', (str(chat_id),)).fetchone()
        if curr:
            await update.message.reply_text("⚠️ Channel already exists in list.")
        else:
            conn.execute('INSERT INTO channels (chat_id, invite_link) VALUES (?, ?)', (str(chat_id), invite_link))
            conn.commit()
            await update.message.reply_text(
                f"✅ **Channel Added!**\n\n"
                f"📌 Title: {chat.title if 'chat' in locals() else 'Unknown'}\n"
                f"🆔 ID: `{chat_id}`\n"
                f"🔗 Link: {invite_link}",
                parse_mode='Markdown'
            )
        conn.close()

    except Exception as e:
        traceback.print_exc()
        await update.message.reply_text("❌ Error processing request. Ensure Bot is Admin in that channel.")

async def del_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /del_channel <id>")
        return
    try:
        chat_id = args[0]
        conn = get_db_connection()
        conn.execute('DELETE FROM channels WHERE chat_id = ?', (chat_id,))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"✅ Channel {chat_id} deleted!")
    except:
        await update.message.reply_text("❌ Error deleting channel.")

# Fallback for list commands if user types them manually, redirect to text response
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return

    # Check if message is a reply or has args
    msg = None
    if update.message.reply_to_message:
        msg = update.message.reply_to_message
    else:
        args = context.args
        if not args:
            await update.message.reply_text("Usage:\n1. Reply to a message with /broadcast\n2. Or type /broadcast <message>")
            return
        msg = " ".join(args)

    conn = get_db_connection()
    users = conn.execute('SELECT user_id FROM users').fetchall()
    conn.close()

    total = len(users)
    sent = 0
    failed = 0

    status_msg = await update.message.reply_text(f"📢 Starting broadcast to {total} users...")

    for user in users:
        try:
            if isinstance(msg, str):
                await context.bot.send_message(chat_id=user['user_id'], text=msg)
            else:
                await msg.copy(chat_id=user['user_id'])
            sent += 1
        except Exception:
            failed += 1
        
        # Avoid flood limits
        if sent % 20 == 0:
            await asyncio.sleep(1)

    await status_msg.edit_text(f"✅ Broadcast Complete!\n\nSent: {sent}\nFailed: {failed}")

async def list_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Reuse button logic or just simple text
    await update.message.reply_text("Please use the dashboard buttons.")

async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please use the dashboard buttons.")

if __name__ == '__main__':
    if not ADMIN_BOT_TOKEN: exit(1)
    application = ApplicationBuilder().token(ADMIN_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    application.add_handler(CommandHandler('add_service', add_service))
    application.add_handler(CommandHandler('add_channel', add_channel))
    application.add_handler(CommandHandler('del_channel', del_channel))
    application.add_handler(CommandHandler('broadcast', broadcast))
    
    print("Admin Bot Running...")
    application.run_polling()
