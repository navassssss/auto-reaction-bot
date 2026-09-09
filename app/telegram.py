import httpx
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class TelegramReactionService:
    def __init__(self):
        self.api_url = "https://api.telegram.org/bot{token}/{method}"

    async def validate_bot(self, token: str) -> Optional[int]:
        """Validates a bot token by calling getMe and returns the bot's user ID."""
        url = self.api_url.format(token=token, method="getMe")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        return data["result"]["id"]
            except Exception as e:
                logger.error(f"Error validating bot token: {e}")
        return None

    async def validate_chat(self, token: str, chat_id: str | int) -> bool:
        """Validates if the bot has access to the chat by calling getChat."""
        url = self.api_url.format(token=token, method="getChat")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json={"chat_id": chat_id}, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("ok", False)
            except Exception as e:
                logger.error(f"Error validating chat {chat_id}: {e}")
        return False

    async def set_reaction(self, token: str, chat_id: str | int, message_id: int, emoji: str) -> Dict[str, Any]:
        """
        Sets a reaction on a message.
        Calls the official Telegram Bot API 'setMessageReaction' method.
        Requires the bot to be an administrator or have appropriate permissions in the chat.
        """
        url = self.api_url.format(token=token, method="setMessageReaction")
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "reaction": [{"type": "emoji", "emoji": emoji}],
            "is_big": False
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=15.0)
                data = response.json()
                return {
                    "status_code": response.status_code,
                    "data": data
                }
            except Exception as e:
                logger.error(f"Exception calling setMessageReaction: {e}")
                return {
                    "status_code": 500,
                    "error": str(e)
                }

telegram_service = TelegramReactionService()
