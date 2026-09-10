import asyncio
import httpx

async def get_message_reactions():
    # Telegram API doesn't have a simple getMessage, but we can forward the message to the bot or something.
    # Actually, if we try to set a reaction and it's full, we get REACTION_INVALID.
    # Let's try setting an emoji that is ALREADY on the message to see if it works.
    pass
