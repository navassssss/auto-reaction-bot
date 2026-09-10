import asyncio
import httpx

async def test_invalid_reaction():
    token = "8768461333:AAGYSBXEFwWHVOn2haQb7dQFw8OV3Vi6ic0"
    chat_id = "@efootballsanam"
    message_id = 990
    
    async with httpx.AsyncClient() as client:
        url = f"https://api.telegram.org/bot{token}/setMessageReaction"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "reaction": [{"type": "emoji", "emoji": "random"}],
            "is_big": False
        }
        res = await client.post(url, json=payload)
        print(f"Reaction response: {res.status_code} - {res.text}")

if __name__ == "__main__":
    asyncio.run(test_invalid_reaction())
