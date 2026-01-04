from src.services.telegram import TelegramBot
from src.core.settings import settings

class Notifier:
    def __init__(self):
        self.telegram = TelegramBot()

    async def send(self, message: str):
        if settings.enable_telegram:
            await self.telegram.send_message(message)

    async def send_signal(self, formatted_signal: str):
        if settings.enable_telegram and settings.send_signals:
            await self.telegram.send_signal(formatted_signal)

    async def close(self):
        await self.telegram.close()
