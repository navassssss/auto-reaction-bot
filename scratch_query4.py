import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT telegram_chat_id, message_id FROM reaction_jobs WHERE job_id = 'JOB-0008031A'"))
        row = result.fetchone()
        print(f"Chat ID: {row[0]}, Message ID: {row[1]}")

if __name__ == "__main__":
    asyncio.run(main())
