import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings

logger = logging.getLogger(__name__)

bot: Bot | None = None
dp = Dispatcher()

async def start_bot():
    global bot
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN is not set. Admin bot will not start.")
        return

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Import handlers to register them
    import app.bot.handlers
    
    # Register webhook if we are running in production/render
    webhook_url = f"https://{settings.host}:{settings.port}/telegram/webhook" # This might be dynamic based on Render env vars or custom env var
    # In Render, we might want a specific PUBLIC_URL env var, or handle it via a setup script.
    
    logger.info("Bot initialized.")

async def stop_bot():
    if bot:
        await bot.session.close()

async def process_update(update_dict: dict):
    if bot:
        from aiogram.types import Update
        update = Update(**update_dict)
        await dp.feed_update(bot, update)
