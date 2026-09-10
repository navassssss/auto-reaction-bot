import asyncio
import random
import logging
from sqlalchemy import select, update, and_
from datetime import datetime, timezone
from app.database import AsyncSessionLocal
from app.models import ReactionTask, ReactionJob, ReactionBot
from app.telegram import telegram_service

logger = logging.getLogger(__name__)

class WorkerManager:
    def __init__(self, worker_count: int = 2):
        self.worker_count = worker_count
        self.workers = []
        self._stop_event = asyncio.Event()

    async def start(self):
        logger.info(f"Starting {self.worker_count} workers...")
        self._stop_event.clear()
        
        # Recover interrupted tasks
        await self.recover_tasks()
        
        for i in range(self.worker_count):
            task = asyncio.create_task(self.worker_loop(i))
            self.workers.append(task)

    async def stop(self):
        logger.info("Stopping workers...")
        self._stop_event.set()
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

    async def recover_tasks(self):
        """Move 'running' tasks back to 'pending' on startup."""
        async with AsyncSessionLocal() as session:
            stmt = update(ReactionTask).where(ReactionTask.status == "running").values(status="pending")
            await session.execute(stmt)
            await session.commit()
            logger.info("Recovered running tasks to pending.")

    async def worker_loop(self, worker_id: int):
        logger.info(f"Worker {worker_id} started.")
        while not self._stop_event.is_set():
            try:
                task_data = await self.claim_task()
                if not task_data:
                    await asyncio.sleep(2)
                    continue

                task_id, job_id, bot_token, chat_id, message_id, emoji = task_data
                await self.process_task(worker_id, task_id, job_id, bot_token, chat_id, message_id, emoji)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} encountered an error: {e}")
                await asyncio.sleep(5)
        
        logger.info(f"Worker {worker_id} stopped.")

    async def claim_task(self):
        """Claims a single pending task and marks it as running using a transaction."""
        async with AsyncSessionLocal() as session:
            # PostgreSQL specific: SKIP LOCKED
            # Since we are using SQLAlchemy ORM, we can use text() or specialized constructs
            from sqlalchemy import text
            
            # Use raw SQL for the claim to utilize RETURNING and FOR UPDATE SKIP LOCKED
            sql = text("""
                UPDATE reaction_tasks
                SET status = 'running', started_at = NOW(), attempts = attempts + 1
                WHERE id = (
                    SELECT id FROM reaction_tasks
                    WHERE status = 'pending'
                    ORDER BY created_at ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                RETURNING id, job_id, bot_id;
            """)
            result = await session.execute(sql)
            row = result.fetchone()
            
            if not row:
                return None
                
            task_id, job_id, bot_id = row
            
            # Fetch related data needed for processing
            job_sql = text("SELECT telegram_chat_id, message_id, emoji FROM reaction_jobs WHERE job_id = :job_id")
            job_res = await session.execute(job_sql, {"job_id": job_id})
            job_row = job_res.fetchone()
            
            bot_sql = text("SELECT token_encrypted FROM reaction_bots WHERE telegram_bot_id = :bot_id")
            bot_res = await session.execute(bot_sql, {"bot_id": bot_id})
            bot_row = bot_res.fetchone()
            
            await session.commit()
            
            if not job_row or not bot_row:
                logger.error(f"Task {task_id}: Job or Bot data missing.")
                await self.mark_task_failed(task_id, "Missing job or bot data")
                return None
                
            chat_id, message_id, emoji = job_row
            bot_token = bot_row[0] # Note: Should decrypt token here in a real app, assuming plaintext/simple encryption for now
            
            return task_id, job_id, bot_token, chat_id, message_id, emoji

    async def process_task(self, worker_id: int, task_id: int, job_id: str, bot_token: str, chat_id: int, message_id: int, emoji: str):
        logger.info(f"Worker {worker_id} processing task {task_id} for job {job_id}")
        
        emoji_to_send = emoji.strip()
        if emoji_to_send.lower() == 'random':
            emoji_to_send = random.choice(['👍', '❤', '🔥', '🥰', '👏', '🎉', '🤩'])
            
        response = await telegram_service.set_reaction(bot_token, chat_id, message_id, emoji_to_send)
        
        if response.get("status_code") == 200 and response.get("data", {}).get("ok"):
            await self.mark_task_success(task_id, bot_token)
        else:
            status_code = response.get("status_code")
            data = response.get("data", {})
            error_msg = data.get("description", response.get("error", "Unknown error"))
            
            if status_code == 429:
                retry_after = data.get("parameters", {}).get("retry_after", 30)
                logger.warning(f"Task {task_id} hit rate limit. Retry after {retry_after}s.")
                await asyncio.sleep(min(retry_after, 10)) 
                await self.requeue_task(task_id)
            else:
                await self.mark_task_failed(task_id, f"{error_msg} (Sent: {repr(emoji_to_send)})", status_code)
        
        await self.update_job_status(job_id)

    async def mark_task_success(self, task_id: int, bot_token: str):
        async with AsyncSessionLocal() as session:
            stmt = update(ReactionTask).where(ReactionTask.id == task_id).values(
                status="success", completed_at=datetime.now(timezone.utc)
            )
            await session.execute(stmt)
            await session.commit()

    async def mark_task_failed(self, task_id: int, error_message: str, error_code: int = None):
        async with AsyncSessionLocal() as session:
            stmt = update(ReactionTask).where(ReactionTask.id == task_id).values(
                status="failed", error_message=error_message, error_code=error_code, completed_at=datetime.now(timezone.utc)
            )
            await session.execute(stmt)
            await session.commit()
            
    async def requeue_task(self, task_id: int):
        async with AsyncSessionLocal() as session:
            stmt = update(ReactionTask).where(ReactionTask.id == task_id).values(
                status="pending"
            )
            await session.execute(stmt)
            await session.commit()

    async def update_job_status(self, job_id: str):
        # Recalculate job status based on tasks
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            sql = text("""
                WITH task_counts AS (
                    SELECT 
                        job_id,
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'success') as successful,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed,
                        COUNT(*) FILTER (WHERE status = 'pending' OR status = 'running') as pending
                    FROM reaction_tasks
                    WHERE job_id = :job_id
                    GROUP BY job_id
                )
                UPDATE reaction_jobs j
                SET 
                    total_tasks = tc.total,
                    successful_tasks = tc.successful,
                    failed_tasks = tc.failed,
                    pending_tasks = tc.pending,
                    status = CASE 
                        WHEN tc.pending > 0 THEN 'running'
                        WHEN tc.failed = 0 THEN 'completed'
                        WHEN tc.successful > 0 THEN 'partially_completed'
                        ELSE 'failed'
                    END,
                    completed_at = CASE
                        WHEN tc.pending = 0 THEN NOW()
                        ELSE NULL
                    END
                FROM task_counts tc
                WHERE j.job_id = tc.job_id;
            """)
            await session.execute(sql, {"job_id": job_id})
            await session.commit()

from app.config import settings
worker_manager = WorkerManager(worker_count=settings.worker_count)

async def start_workers():
    await worker_manager.start()

async def stop_workers():
    await worker_manager.stop()
