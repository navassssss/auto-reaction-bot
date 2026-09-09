import re
import uuid
from datetime import datetime, timezone
from aiogram import types, F
from aiogram.filters import Command, CommandStart, CommandObject
from sqlalchemy import select, update, func, delete
import logging

from app.bot.main import dp
from app.database import AsyncSessionLocal
from app.models import AuthorizedChannel, ReactionBot, ReactionJob, ReactionTask, AuditLog
from app.telegram import telegram_service

logger = logging.getLogger(__name__)

def parse_telegram_url(url: str):
    # e.g. https://t.me/my_channel/123
    match = re.match(r"https?://t\.me/(?:c/)?([a-zA-Z0-9_]+)/(\d+)", url)
    if match:
        return match.group(1), int(match.group(2))
    return None, None

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Welcome to the Auto Reaction Admin Bot.\n"
        "Commands:\n"
        "/react <telegram_post_link> <emoji> - Create a reaction job\n"
        "/status <job_id> - Check job status\n"
        "/cancel <job_id> - Cancel a job\n"
        "/bots - Manage reaction bots\n"
        "/addbot <token> <name> - Add a new reaction bot\n"
        "/channels - Manage authorized channels\n"
        "/addchannel <id_or_username> <title> - Add an authorized channel\n"
        "/help - Show help"
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await cmd_start(message)

@dp.message(Command("react"))
async def cmd_react(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer("Usage: /react <telegram_post_link> <emoji>")
        return
        
    parts = command.args.split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Usage: /react <telegram_post_link> <emoji>")
        return
        
    url, emoji = parts
    channel_identifier, message_id = parse_telegram_url(url)
    
    if not channel_identifier or not message_id:
        await message.answer("Invalid Telegram URL. Example: https://t.me/my_channel/123")
        return
        
    async with AsyncSessionLocal() as session:
        # Validate channel
        stmt = select(AuthorizedChannel).where(
            (AuthorizedChannel.username == channel_identifier) | 
            (AuthorizedChannel.telegram_chat_id == (int(channel_identifier) if channel_identifier.lstrip('-').isdigit() else 0))
        ).where(AuthorizedChannel.enabled == True)
        
        result = await session.execute(stmt)
        channel = result.scalars().first()
        
        if not channel:
            await message.answer("Destination is not authorized or is disabled. Add it via /channels first.")
            return

        # Load bots
        bots_stmt = select(ReactionBot).where(ReactionBot.enabled == True)
        bots_res = await session.execute(bots_stmt)
        bots = bots_res.scalars().all()
        
        if not bots:
            await message.answer("No enabled bots available.")
            return
            
        job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
        
        job = ReactionJob(
            job_id=job_id,
            telegram_chat_id=channel.telegram_chat_id,
            message_id=message_id,
            post_url=url,
            emoji=emoji,
            status="queued",
            total_tasks=len(bots),
            pending_tasks=len(bots)
        )
        session.add(job)
        
        for bot in bots:
            task = ReactionTask(
                job_id=job_id,
                bot_id=bot.telegram_bot_id,
                status="pending"
            )
            session.add(task)
            
        audit = AuditLog(
            admin_telegram_id=message.from_user.id,
            action="create_job",
            job_id=job_id,
            target_chat_id=channel.telegram_chat_id,
            target_message_id=message_id,
            metadata_={"emoji": emoji, "bots_count": len(bots)}
        )
        session.add(audit)
        
        await session.commit()
        
        await message.answer(
            f"Reaction job created.\n\n"
            f"Job ID: {job_id}\n"
            f"Post: @{channel_identifier}/{message_id}\n"
            f"Reaction: {emoji}\n"
            f"Bots: {len(bots)}\n"
            f"Status: queued"
        )

@dp.message(Command("status"))
async def cmd_status(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer("Usage: /status <job_id>")
        return
        
    job_id = command.args.strip()
    
    async with AsyncSessionLocal() as session:
        stmt = select(ReactionJob).where(ReactionJob.job_id == job_id)
        res = await session.execute(stmt)
        job = res.scalars().first()
        
        if not job:
            await message.answer("Job not found.")
            return
            
        await message.answer(
            f"Job: {job.job_id}\n"
            f"Status: {job.status}\n\n"
            f"Post: {job.post_url}\n"
            f"Reaction: {job.emoji}\n\n"
            f"Total: {job.total_tasks}\n"
            f"Successful: {job.successful_tasks}\n"
            f"Failed: {job.failed_tasks}\n"
            f"Pending: {job.pending_tasks}"
        )

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer("Usage: /cancel <job_id>")
        return
        
    job_id = command.args.strip()
    
    async with AsyncSessionLocal() as session:
        stmt = select(ReactionJob).where(ReactionJob.job_id == job_id)
        res = await session.execute(stmt)
        job = res.scalars().first()
        
        if not job:
            await message.answer("Job not found.")
            return
            
        if job.status in ["completed", "failed", "cancelled"]:
            await message.answer(f"Job is already {job.status}.")
            return
            
        # Cancel pending tasks
        update_stmt = update(ReactionTask).where(
            ReactionTask.job_id == job_id,
            ReactionTask.status.in_(["pending", "running"])
        ).values(status="cancelled", completed_at=datetime.now(timezone.utc))
        
        await session.execute(update_stmt)
        
        # Update job status
        job.status = "cancelled"
        
        audit = AuditLog(
            admin_telegram_id=message.from_user.id,
            action="cancel_job",
            job_id=job_id
        )
        session.add(audit)
        
        await session.commit()
        
        await message.answer(
            f"Job {job_id} cancelled. Pending tasks have been cancelled.\n"
            "Note: Already completed API operations cannot be undone."
        )

@dp.message(Command("bots"))
async def cmd_bots(message: types.Message):
    async with AsyncSessionLocal() as session:
        stmt = select(ReactionBot)
        res = await session.execute(stmt)
        bots = res.scalars().all()
        
        enabled_count = sum(1 for b in bots if b.enabled)
        disabled_count = len(bots) - enabled_count
        
        text = f"Reaction bots\n\nEnabled: {enabled_count}\nDisabled: {disabled_count}\n\n"
        
        for b in bots:
            text += (
                f"Name: {b.name}\n"
                f"Status: {'Enabled' if b.enabled else 'Disabled'}\n"
                f"Last success: {b.last_success_at or 'Never'}\n"
                f"Last error: {b.last_error_at or 'None'}\n\n"
            )
            
        # Inline buttons would be added here in a real implementation for Enable/Disable/Delete
        await message.answer(text)

@dp.message(Command("channels"))
async def cmd_channels(message: types.Message):
    async with AsyncSessionLocal() as session:
        stmt = select(AuthorizedChannel)
        res = await session.execute(stmt)
        channels = res.scalars().all()
        
        if not channels:
            await message.answer("No authorized channels.")
            return
            
        text = "Authorized Channels:\n\n"
        for c in channels:
            text += f"{c.title or c.username} ({c.telegram_chat_id}) - {'Enabled' if c.enabled else 'Disabled'}\n"
            
        await message.answer(text)

@dp.message(Command("addbot"))
async def cmd_addbot(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer("Usage: /addbot <token> <name>")
        return
        
    parts = command.args.split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Usage: /addbot <token> <name>")
        return
        
    token, name = parts
    
    bot_id = await telegram_service.validate_bot(token)
    if not bot_id:
        await message.answer("Invalid bot token. Telegram API rejected it.")
        return
        
    async with AsyncSessionLocal() as session:
        # Check if already exists
        stmt = select(ReactionBot).where(ReactionBot.telegram_bot_id == bot_id)
        existing = await session.execute(stmt)
        if existing.scalars().first():
            await message.answer("This bot is already registered.")
            return
            
        new_bot = ReactionBot(
            name=name,
            telegram_bot_id=bot_id,
            token_encrypted=token, # In a real app, encrypt this
            enabled=True
        )
        session.add(new_bot)
        
        audit = AuditLog(
            admin_telegram_id=message.from_user.id,
            action="add_bot",
            metadata_={"bot_id": bot_id, "name": name}
        )
        session.add(audit)
        
        await session.commit()
        
    await message.answer(f"Bot '{name}' successfully registered and verified!")

@dp.message(Command("addchannel"))
async def cmd_addchannel(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer("Usage: /addchannel <chat_id_or_username> <title>")
        return
        
    parts = command.args.split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Usage: /addchannel <chat_id_or_username> <title>")
        return
        
    identifier, title = parts
    
    # Parse identifier
    try:
        chat_id = int(identifier)
        username = None
    except ValueError:
        chat_id = 0 # Not known yet, must rely on username matching if used this way
        username = identifier.replace('@', '')
        
    # Telegram requires accurate chat_ids for API calls usually, so encourage numeric.
    if chat_id == 0 and not username:
        await message.answer("Invalid identifier. Please provide a numeric ID (e.g. -100123...) or username.")
        return
        
    async with AsyncSessionLocal() as session:
        # Check if already exists
        if chat_id != 0:
            stmt = select(AuthorizedChannel).where(AuthorizedChannel.telegram_chat_id == chat_id)
        else:
            stmt = select(AuthorizedChannel).where(AuthorizedChannel.username == username)
            
        existing = await session.execute(stmt)
        if existing.scalars().first():
            await message.answer("This channel is already authorized.")
            return
            
        # For simplicity, if they provided a username, we set chat_id to a dummy or try to resolve it.
        # Actually we need telegram_chat_id as NOT NULL UNIQUE in our schema.
        # If they only gave a username, we can't easily insert 0 if another one has 0. 
        # We must require the numeric ID.
        if chat_id == 0:
            await message.answer("Please provide the numeric Telegram Chat ID (starts with -100...). Usernames alone cannot be reliably stored without an ID in our current schema.")
            return

        new_channel = AuthorizedChannel(
            telegram_chat_id=chat_id,
            username=username,
            title=title,
            enabled=True
        )
        session.add(new_channel)
        
        audit = AuditLog(
            admin_telegram_id=message.from_user.id,
            action="add_channel",
            target_chat_id=chat_id,
            metadata_={"title": title}
        )
        session.add(audit)
        
        await session.commit()
        
    await message.answer(f"Channel '{title}' successfully authorized!")
