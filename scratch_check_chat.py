import asyncio
import httpx

async def check_chat():
    token = "8768461333:AAGYSBXEFwWHVOn2haQb7dQFw8OV3Vi6ic0"
    chat_id = "@efootballsanam" 
    
    async with httpx.AsyncClient() as client:
        url = f"https://api.telegram.org/bot{token}/getChat"
        res = await client.post(url, json={"chat_id": chat_id})
        print(f"getChat response: {res.status_code} - {res.text}")

if __name__ == "__main__":
    asyncio.run(check_chat())
