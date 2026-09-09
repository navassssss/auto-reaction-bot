from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from app.config import settings

class AdminAuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id
            
        if user_id:
            if user_id not in settings.admin_ids_list:
                if isinstance(event, Message):
                    await event.answer("Access denied.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("Access denied.", show_alert=True)
                return # Stop processing
                
        return await handler(event, data)
