import logging
import asyncio
import aiohttp
from src.core.settings import settings

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.session = None

    async def _get_session(self):
        if self.session is None or self.session.closed:
            # Disable SSL verification as per original code workaround
            self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
        return self.session

    async def send_message(self, message: str, chat_id: str = None):
        if not settings.enable_telegram or not settings.send_signals:
            return

        target_chat_id = chat_id or self.chat_id
        session = await self._get_session()
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": target_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Telegram send failed: {await response.text()}")
        except Exception as e:
            logger.error(f"Telegram error: {e}")

    async def send_signal(self, formatted_signal: str):
        await self.send_message(formatted_signal)

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
