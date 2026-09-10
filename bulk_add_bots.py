import asyncio
import os
import re
from sqlalchemy import select
from app.database import AsyncSessionLocal, engine
from app.models import ReactionBot, Base
from app.telegram import telegram_service

async def main():
    if not os.path.exists("bots.txt"):
        print("bots.txt not found!")
        return

    with open("bots.txt", "r") as f:
        lines = f.readlines()

    tokens = []
    # Extract tokens looking for standard format NNNNNNNNN:XXXXXXX
    for line in lines:
        match = re.search(r"(\d{8,10}:[a-zA-Z0-9_-]{35,})", line)
        if match:
            tokens.append(match.group(1))

    if not tokens:
        print("No valid tokens found in bots.txt.")
        return

    print(f"Found {len(tokens)} tokens to import.")

    async with AsyncSessionLocal() as session:
        for idx, token in enumerate(tokens):
            print(f"Validating bot {idx+1}/{len(tokens)}...")
            bot_id = await telegram_service.validate_bot(token)
            
            if not bot_id:
                print(f"  [X] Failed! Telegram rejected token: {token[:15]}...")
                continue

            # Check if it exists
            stmt = select(ReactionBot).where(ReactionBot.telegram_bot_id == bot_id)
            existing = await session.execute(stmt)
            if existing.scalars().first():
                print(f"  [-] Skipped. Bot ID {bot_id} already exists in database.")
                continue

            name = f"ImportedBot_{bot_id}"
            new_bot = ReactionBot(
                name=name,
                telegram_bot_id=bot_id,
                token_encrypted=token,
                enabled=True
            )
            session.add(new_bot)
            print(f"  [+] Added Bot ID {bot_id} successfully.")

        await session.commit()
        print("Done importing bots!")

if __name__ == "__main__":
    asyncio.run(main())
