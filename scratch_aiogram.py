import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Update

async def main():
    bot = Bot(token="1234:test")
    dp = Dispatcher()
    
    @dp.message()
    async def handler(msg):
        print("Message received!")
        
    update_dict = {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "date": 1234567890,
            "chat": {"id": 1, "type": "private"},
            "from": {"id": 1, "is_bot": False, "first_name": "Test"},
            "text": "/start"
        }
    }
    
    try:
        update = Update(**update_dict)
        print("Update parsed successfully")
        await dp.feed_update(bot, update)
        print("Update fed successfully")
    except Exception as e:
        print(f"Error: {e}")
        
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
