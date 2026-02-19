import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from config import USER_BOT_TOKEN, ADMIN_BOT_TOKEN, WEB_APP_URL, ADMIN_ID
from user_bot import start as user_start, btn_handler as user_btn_handler, post_init as user_post_init
from admin_bot import start as admin_start, add_service, list_orders, add_channel, del_channel, list_channels, button_handler, broadcast
from database import init_db
import traceback

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    # 1. Initialize Database
    init_db()
    logger.info("Database initialized.")

    # 2. Build User Bot Application
    user_app = ApplicationBuilder().token(USER_BOT_TOKEN).post_init(user_post_init).build()
    user_app.add_handler(CommandHandler('start', user_start))
    user_app.add_handler(CallbackQueryHandler(user_btn_handler))

    # 3. Build Admin Bot Application
    admin_app = ApplicationBuilder().token(ADMIN_BOT_TOKEN).build()
    admin_app.add_handler(CommandHandler('start', admin_start))
    admin_app.add_handler(CommandHandler('add_service', add_service))
    admin_app.add_handler(CommandHandler('orders', list_orders))
    admin_app.add_handler(CommandHandler('add_channel', add_channel))
    admin_app.add_handler(CommandHandler('del_channel', del_channel))
    admin_app.add_handler(CommandHandler('channels', list_channels))
    admin_app.add_handler(CommandHandler('broadcast', broadcast))
    admin_app.add_handler(CallbackQueryHandler(button_handler))

    # 4. Run both bots concurrently
    logger.info("Starting bots...")
    
    # We use update_queue to run them in parallel if needed, but initialize_ and start_ are better for custom loops
    # However, simpler is to just run_polling in parallel tasks
    
    async with user_app:
        await user_app.start()
        await user_app.updater.start_polling()
        
        async with admin_app:
            await admin_app.start()
            await admin_app.updater.start_polling()
            
            # Keep the main loop running
            logger.info("Bots are running. Press Ctrl+C to stop.")
            # We need a forever loop here that doesn't block
            stop_signal = asyncio.Event()
            await stop_signal.wait()
            
            await admin_app.updater.stop()
            await admin_app.stop()
        
        await user_app.updater.stop()
        await user_app.stop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        traceback.print_exc()
