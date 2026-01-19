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
        self.running = False
        self.bot_control_callback = None # Callback to control main bot (start/stop)

    async def _get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
        return self.session

    def set_control_callback(self, callback):
        self.bot_control_callback = callback

    async def start_polling(self):
        """Starts the polling loop for handling updates"""
        # [DISABLED] polling to avoid 409 Conflict with external instances
        logger.info("Telegram polling is DISABLED. Bot can still SEND signals.")
        return

    async def stop(self):
        self.running = False
        await self.close()

    async def _process_update(self, update):
        message = update.get('message', {})
        text = message.get('text', '')
        chat_id = str(message.get('chat', {}).get('id', ''))

        if not text: return

        # Security check (allow only configured user or admin)
        if chat_id != str(self.chat_id) and chat_id != str(settings.telegram_admin_chat_id):
            logger.warning(f"Unauthorized command from {chat_id}: {text}")
            return

        if text.startswith('/'):
            await self._handle_command(text, chat_id)

    async def _handle_command(self, command: str, chat_id: str):
        cmd = command.split()[0]
        logger.info(f"Received command: {cmd} from {chat_id}")
        
        if cmd == '/start' or cmd == '/startbot':
            msg = "🤖 <b>Bot Started!</b>\nAnalyze loop is running."
            if self.bot_control_callback:
                self.bot_control_callback('start')
            await self.send_message(msg, chat_id)
            
        elif cmd == '/stop' or cmd == '/stopbot':
            msg = "🛑 <b>Bot Paused!</b>\nAnalysis loop stopped."
            if self.bot_control_callback:
                self.bot_control_callback('stop')
            await self.send_message(msg, chat_id)
            
        elif cmd == '/status':
            msg = "ℹ️ <b>Status</b>: Running\nMode: Multi-Strategy"
            await self.send_message(msg, chat_id)
            
        elif cmd == '/help':
            msg = (
                "<b>Commands:</b>\n"
                "/startbot - Start Bot\n"
                "/stopbot - Pause Bot\n"
                "/status - Check Status\n"
            )
            await self.send_message(msg, chat_id)

    async def send_message(self, message: any, chat_id: str = None):
        if not settings.enable_telegram: return
        
        # Format message if it's a signal object
        if hasattr(message, 'to_html'):
            message = message.to_html()
        else:
            message = str(message)

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
                if response.status == 200:
                    logger.info(f"✅ Telegram message sent successfully to {target_chat_id}")
                else:
                    logger.error(f"Telegram send failed: {await response.text()}")
        except Exception as e:
            logger.error(f"Telegram error: {e}")

    async def send_signal(self, signal_data: any):
        if settings.send_signals:
            await self.send_message(signal_data)

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
