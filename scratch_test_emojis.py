import asyncio
import httpx

async def test_emojis():
    token = "8768461333:AAGYSBXEFwWHVOn2haQb7dQFw8OV3Vi6ic0"
    chat_id = "@efootballsanam" # from post URL: https://t.me/efootballsanam/990
    message_id = 990
    
    emojis = ['👍', '❤', '🔥', '🥰', '👏', '🎉', '🤩', '💯', '⚡', '🏆']
    # Let's also test ❤️
    emojis.append('❤️')
    emojis.append('⚡️')
    emojis.append('💯')
    
    async with httpx.AsyncClient() as client:
        for e in emojis:
            url = f"https://api.telegram.org/bot{token}/setMessageReaction"
            payload = {
                "chat_id": chat_id,
                "message_id": message_id,
                "reaction": [{"type": "emoji", "emoji": e}],
                "is_big": False
            }
            res = await client.post(url, json=payload)
            print(f"Emoji {ascii(e)} ({e}): {res.status_code} - {res.text}")

if __name__ == "__main__":
    asyncio.run(test_emojis())
