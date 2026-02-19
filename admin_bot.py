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
    if update.effective_user.id != int(ADMIN_ID):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⛔ Access Denied.")
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="👑 Admin Panel 👑\n\nCommands:\n/add_service <name> <price> <desc>\n/orders - View recent orders"
    )

async def add_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != int(ADMIN_ID):
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
    if update.effective_user.id != int(ADMIN_ID):
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

if __name__ == '__main__':
    application = ApplicationBuilder().token(ADMIN_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    add_service_handler = CommandHandler('add_service', add_service)
    orders_handler = CommandHandler('orders', list_orders)
    
    application.add_handler(start_handler)
    application.add_handler(add_service_handler)
    application.add_handler(orders_handler)
    
    print("Admin Bot is running...")
    application.run_polling()
