import asyncio
import httpx

async def test_bot():
    token = "8925837492:AAHtvgVBwzhxOR4GSo8uodc-Eu0bitcT7lE"
    chat_id = "@efootballsanam"
    message_id = 990
    
    async with httpx.AsyncClient() as client:
        url = f"https://api.telegram.org/bot{token}/setMessageReaction"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "reaction": [{"type": "emoji", "emoji": "👍"}],
            "is_big": False
        }
        res = await client.post(url, json=payload)
        print(f"Reaction response: {res.status_code} - {res.text}")

if __name__ == "__main__":
    asyncio.run(test_bot())
