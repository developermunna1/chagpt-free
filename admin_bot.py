import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler
from config import ADMIN_BOT_TOKEN, ADMIN_ID
from database import get_db_connection

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Check for ADMIN_ID validity
    if not ADMIN_ID:
        await context.bot.send_message(chat_id=user_id, text="⚠️ Critical Error: ADMIN_ID not configured in settings.")
        return

    try:
        admin_id_int = int(ADMIN_ID)
    except (ValueError, TypeError):
        await context.bot.send_message(chat_id=user_id, text="⚠️ Critical Error: ADMIN_ID in settings is not a number.")
        return

    if user_id != admin_id_int:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⛔ Access Denied. You are not the admin.")
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "👑 Admin Panel 👑\n\n"
            "Service Management:\n"
            "/add_service <name> <price> <desc>\n"
            "/orders - View recent orders\n\n"
            "Channel Verification:\n"
            "/add_channel <id> <link> - Add required channel\n"
            "/del_channel <id> - Remove channel\n"
            "/channels - List all channels"
        )
        # Removed parse_mode to avoid Markdown errors
    )

async def add_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_ID or update.effective_user.id != int(ADMIN_ID):
        return

    try:
        # Expected format: /add_service ServiceName 10.50 Description here
        args = context.args
        if len(args) < 3:
            await update.message.reply_text("Usage: /add_service <name> <price> <description>")
            return

        name = args[0]
        price = float(args[1])
        description = " ".join(args[2:])

        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT INTO services (name, price, description) VALUES (?, ?, ?)', (name, price, description))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"✅ Service '{name}' added successfully!")

    except ValueError:
        await update.message.reply_text("❌ Error: Price must be a number.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        await update.message.reply_text("❌ An error occurred.")

async def list_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_ID or update.effective_user.id != int(ADMIN_ID):
        return

    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM orders ORDER BY timestamp DESC LIMIT 10')
    orders = c.fetchall()
    conn.close()

    if not orders:
        await update.message.reply_text("📭 No orders found.")
        return

    message = "📦 **Recent Orders**:\n\n"
    for order in orders:
        message += f"ID: {order['id']} | User: {order['user_id']} | Service: {order['service_id']}\nStatus: {order['status']}\n\n"

    await update.message.reply_text(message)

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_ID or update.effective_user.id != int(ADMIN_ID):
        return

    try:
        # Expected format: /add_channel -100123456789 https://t.me/+AbCdEfGh
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Usage: /add_channel <chat_id> <invite_link>")
            return

        chat_id = args[0]
        # Joining the rest as link in case it has spaces (though unlikely for links)
        invite_link = args[1]

        conn = get_db_connection()
        c = conn.cursor()
        # Check if exists
        curr = c.execute('SELECT * FROM channels WHERE chat_id = ?', (chat_id,)).fetchone()
        if curr:
            await update.message.reply_text("⚠️ Channel already exists.")
            conn.close()
            return

        c.execute('INSERT INTO channels (chat_id, invite_link) VALUES (?, ?)', (chat_id, invite_link))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"✅ Channel {chat_id} added successfully!")

    except Exception as e:
        import traceback
        traceback.print_exc()
        await update.message.reply_text("❌ An error occurred.")

async def del_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_ID or update.effective_user.id != int(ADMIN_ID):
        return

    try:
        args = context.args
        if len(args) < 1:
            await update.message.reply_text("Usage: /del_channel <chat_id>")
            return

        chat_id = args[0]

        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM channels WHERE chat_id = ?', (chat_id,))
        rows = c.rowcount
        conn.commit()
        conn.close()

        if rows > 0:
            await update.message.reply_text(f"✅ Channel {chat_id} removed.")
        else:
            await update.message.reply_text(f"⚠️ Channel {chat_id} not found.")

    except Exception as e:
        await update.message.reply_text("❌ An error occurred.")

async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_ID or update.effective_user.id != int(ADMIN_ID):
        return

    conn = get_db_connection()
    channels = conn.execute('SELECT * FROM channels').fetchall()
    conn.close()

    if not channels:
        await update.message.reply_text("📭 No channels configured.")
        return

    msg = "📢 **Required Channels:**\n\n"
    for ch in channels:
        msg += f"ID: `{ch['chat_id']}`\nLink: {ch['invite_link']}\n\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

if __name__ == '__main__':
    # Main.py handles the real execution, this is for local testing fallback
    if not ADMIN_BOT_TOKEN:
        print("Error: ADMIN_BOT_TOKEN not set.")
        exit(1)
        
    application = ApplicationBuilder().token(ADMIN_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    add_service_handler = CommandHandler('add_service', add_service)
    orders_handler = CommandHandler('orders', list_orders)
    
    # Channel handlers
    add_channel_handler = CommandHandler('add_channel', add_channel)
    del_channel_handler = CommandHandler('del_channel', del_channel)
    list_channels_handler = CommandHandler('channels', list_channels)

    application.add_handler(start_handler)
    application.add_handler(add_service_handler)
    application.add_handler(orders_handler)
    
    application.add_handler(add_channel_handler)
    application.add_handler(del_channel_handler)
    application.add_handler(list_channels_handler)
    
    print("Admin Bot is running...")
    application.run_polling()
