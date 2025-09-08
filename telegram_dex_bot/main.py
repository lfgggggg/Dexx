#!/usr/bin/env python3
"""
Telegram DEX Bot - Main Entry Point
A Telegram bot for trading on Nad.fun DEX via Somnia/Monad
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from bot.telegram_bot import TelegramDEXBot
from database.db_manager import DatabaseManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main entry point for the Telegram DEX Bot"""
    
    # Validate environment variables
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN environment variable is required")
        return
    
    rpc_url = os.getenv('RPC_URL', 'https://jsonrpc.somnia.network')
    db_path = os.getenv('DB_PATH', 'bot_database.db')
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()
        
        # Initialize and start bot
        logger.info("Starting Telegram DEX Bot...")
        bot = TelegramDEXBot(bot_token, rpc_url, db_manager)
        await bot.start()
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        logger.info("Bot shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")