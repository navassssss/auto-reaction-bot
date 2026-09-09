from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
import logging
import asyncio

from app.config import settings, setup_logging
from app.database import engine
from app.bot.main import start_bot, stop_bot, process_update
from app.workers.manager import start_workers, stop_workers

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Telegram Reaction Manager...")
    
    # Optional: ensure db can connect
    try:
        async with engine.connect() as conn:
            logger.info("Database connection established.")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        
    await start_bot()
    await start_workers()
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await stop_workers()
    await stop_bot()
    await engine.dispose()
    logger.info("Shutdown complete.")

app = FastAPI(title="Telegram Reaction Manager", lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "database": "ok",
        "service": "telegram-reaction-manager"
    }

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if settings.telegram_webhook_secret and secret_token != settings.telegram_webhook_secret:
        logger.warning("Invalid webhook secret token received.")
        raise HTTPException(status_code=401, detail="Invalid secret token")
        
    try:
        update = await request.json()
        await process_update(update)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        # Return 200 anyway so Telegram doesn't keep retrying bad updates endlessly
    
    return {"ok": True}
