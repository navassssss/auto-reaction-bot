import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT emoji FROM reaction_jobs WHERE job_id = 'JOB-0008031A'"))
        row = result.fetchone()
        if row:
            print(f"EMOJI IN DB: {repr(row[0])}")
        else:
            print("Job not found")

if __name__ == "__main__":
    asyncio.run(main())
