import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT t.id, t.bot_id, b.token_encrypted 
            FROM reaction_tasks t
            JOIN reaction_bots b ON t.bot_id = b.telegram_bot_id
            WHERE t.job_id = 'JOB-0008031A'
        """))
        for row in result.fetchall():
            print(dict(row._mapping))

if __name__ == "__main__":
    asyncio.run(main())
