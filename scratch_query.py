import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT id, status, error_message, error_code, attempts FROM reaction_tasks WHERE job_id = 'JOB-6D779859' LIMIT 5"))
        for row in result.fetchall():
            print(dict(row._mapping))

if __name__ == "__main__":
    asyncio.run(main())
