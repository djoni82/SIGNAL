#!/usr/bin/env python3
"""
Telegram Enhanced Signal Bot
Telegram бот с детальными сигналами
"""

import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from typing import Dict, Any, Optional
import time

from enhanced_signal_bot_with_explanations import EnhancedSignalBot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramEnhancedBot:
    """Telegram бот с детальными сигналами"""
    
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.application = None
        self.signal_bot = None
        self.running = False
        
        # Конфигурация для сигнального бота
        self.config = {
            'signals': {
                'min_confidence': 0.3,
                'interval': 300,  # 5 минут между сигналами
                'cycle_interval': 60  # 1 минута между циклами
            },
            'trading_pairs': [
                'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
                'DOT/USDT', 'LINK/USDT', 'MATIC/USDT', 'AVAX/USDT', 'ATOM/USDT'
            ]
        }
        
        logger.info("🤖 Telegram Enhanced Bot инициализирован")
    
    async def start(self):
        """Запускает Telegram бота"""
        try:
            # Создаем приложение
            self.application = Application.builder().token(self.token).build()
            
            # Добавляем обработчики команд
            self.application.add_handler(CommandHandler("start", self.cmd_start))
            self.application.add_handler(CommandHandler("startbot", self.cmd_start_bot))
            self.application.add_handler(CommandHandler("stopbot", self.cmd_stop_bot))
            self.application.add_handler(CommandHandler("status", self.cmd_status))
            self.application.add_handler(CommandHandler("signals", self.cmd_signals))
            self.application.add_handler(CommandHandler("pairs", self.cmd_pairs))
            self.application.add_handler(CommandHandler("help", self.cmd_help))
            
            # Запускаем бота
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            self.running = True
            logger.info("🤖 Telegram бот запущен")
            
            # Держим бота запущенным
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Ошибка запуска Telegram бота: {e}")
    
    async def stop(self):
        """Останавливает Telegram бота"""
        self.running = False
        if self.signal_bot:
            await self.signal_bot.stop()
        
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
        
        logger.info("🛑 Telegram бот остановлен")
    
    async def send_message(self, message: str):
        """Отправляет сообщение в Telegram"""
        try:
            if self.application:
                await self.application.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        welcome_message = """
🚀 <b>CryptoAlphaPro Signal Bot</b>

Добро пожаловать! Я продвинутый бот для генерации торговых сигналов с детальными объяснениями.

<b>Доступные команды:</b>
/startbot - Запустить бота сигналов
/stopbot - Остановить бота сигналов
/status - Статус бота
/signals - Статистика сигналов
/pairs - Список торговых пар
/help - Справка

<b>Особенности:</b>
• Детальные объяснения сигналов
• Технический анализ (RSI, MACD, ADX, Bollinger Bands)
• Паттерны свечей
• Мультитаймфреймовый анализ
• Уровни Take Profit и Stop Loss
• Анализ объемов

Нажмите /startbot для запуска!
        """
        await update.message.reply_text(welcome_message, parse_mode='HTML')
    
    async def cmd_start_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /startbot"""
        try:
            if self.signal_bot and self.signal_bot.running:
                await update.message.reply_text("⚠️ Бот уже запущен!")
                return
            
            # Создаем и запускаем сигнальный бот
            self.signal_bot = EnhancedSignalBot(self.config)
            
            # Переопределяем метод отправки сигналов
            original_send_signal = self.signal_bot.send_signal
            self.signal_bot.send_signal = lambda signal, analysis: self.send_signal_to_telegram(signal, analysis)
            
            # Запускаем в отдельной задаче
            asyncio.create_task(self.signal_bot.start())
            
            await update.message.reply_text("🚀 Бот сигналов запущен! Ожидайте сигналы...")
            logger.info("🚀 Сигнальный бот запущен через Telegram")
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            await update.message.reply_text(f"❌ Ошибка запуска: {e}")
    
    async def cmd_stop_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /stopbot"""
        try:
            if not self.signal_bot or not self.signal_bot.running:
                await update.message.reply_text("⚠️ Бот не запущен!")
                return
            
            await self.signal_bot.stop()
            await update.message.reply_text("🛑 Бот сигналов остановлен!")
            logger.info("🛑 Сигнальный бот остановлен через Telegram")
            
        except Exception as e:
            logger.error(f"❌ Ошибка остановки бота: {e}")
            await update.message.reply_text(f"❌ Ошибка остановки: {e}")
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /status"""
        try:
            if not self.signal_bot:
                status_message = "📊 <b>Статус бота:</b>\n• Сигнальный бот: Не запущен"
            else:
                status = self.signal_bot.get_status()
                status_message = f"""
📊 <b>Статус бота:</b>
• Сигнальный бот: {'🟢 Запущен' if status['running'] else '🔴 Остановлен'}
• Всего сигналов: {status['signal_count']}
• Торговых пар: {status['trading_pairs']}
• Минимальная уверенность: {status['min_confidence']*100:.0f}%
• Последний сигнал: {time.strftime('%H:%M:%S', time.localtime(status['last_signal_time'])) if status['last_signal_time'] > 0 else 'Нет'}
                """
            
            await update.message.reply_text(status_message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса: {e}")
            await update.message.reply_text(f"❌ Ошибка: {e}")
    
    async def cmd_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /signals"""
        try:
            if not self.signal_bot:
                await update.message.reply_text("⚠️ Бот не запущен!")
                return
            
            status = self.signal_bot.get_status()
            signals_message = f"""
📈 <b>Статистика сигналов:</b>
• Всего сигналов: {status['signal_count']}
• Последний сигнал: {time.strftime('%H:%M:%S', time.localtime(status['last_signal_time'])) if status['last_signal_time'] > 0 else 'Нет'}
• Интервал между сигналами: {self.config['signals']['interval']} сек
• Минимальная уверенность: {status['min_confidence']*100:.0f}%
            """
            
            await update.message.reply_text(signals_message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            await update.message.reply_text(f"❌ Ошибка: {e}")
    
    async def cmd_pairs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /pairs"""
        try:
            pairs_message = "📊 <b>Торговые пары:</b>\n\n"
            for i, pair in enumerate(self.config['trading_pairs'], 1):
                pairs_message += f"{i}. {pair}\n"
            
            pairs_message += f"\nВсего пар: {len(self.config['trading_pairs'])}"
            
            await update.message.reply_text(pairs_message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка пар: {e}")
            await update.message.reply_text(f"❌ Ошибка: {e}")
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_message = """
📚 <b>Справка по командам:</b>

<b>Основные команды:</b>
/start - Приветствие и описание бота
/startbot - Запустить генерацию сигналов
/stopbot - Остановить генерацию сигналов
/status - Показать статус бота
/signals - Статистика сигналов
/pairs - Список торговых пар
/help - Эта справка

<b>О сигналах:</b>
• Сигналы генерируются каждые 5 минут
• Минимальная уверенность: 30%
• Включают детальные объяснения
• Показывают уровни TP и SL
• Анализируют технические индикаторы

<b>Технический анализ:</b>
• RSI (Relative Strength Index)
• MACD (Moving Average Convergence Divergence)
• ADX (Average Directional Index)
• Bollinger Bands
• Паттерны свечей
• Анализ объемов

<b>Поддержка:</b>
По всем вопросам обращайтесь к разработчику.
        """
        await update.message.reply_text(help_message, parse_mode='HTML')
    
    async def send_signal_to_telegram(self, signal: Dict[str, Any], analysis: Dict[str, Any]):
        """Отправляет сигнал в Telegram с детальным объяснением"""
        try:
            from signal_explainer import SignalExplainer
            
            explainer = SignalExplainer()
            
            # Создаем мультитаймфреймовый анализ
            mtf_analysis = {
                'timeframes': {
                    '15m': {'trend': 'bullish' if signal['action'] == 'BUY' else 'bearish'},
                    '1h': {'trend': 'bullish' if signal['action'] == 'BUY' else 'bearish'},
                    '4h': {'trend': 'neutral'}
                },
                'overall_trend': 'bullish' if signal['action'] == 'BUY' else 'bearish'
            }
            
            # Генерируем детальное сообщение
            message = explainer.format_signal_message(signal, analysis, mtf_analysis)
            
            # Добавляем статистику
            status = self.signal_bot.get_status()
            message += f"\n📈 <b>Статистика бота:</b>\n"
            message += f"• Всего сигналов: {status['signal_count']}\n"
            message += f"• Последний сигнал: {time.strftime('%H:%M:%S')}\n"
            message += f"• Уверенность: {signal['confidence']*100:.0f}%\n"
            
            # Отправляем в Telegram
            await self.send_message(message)
            logger.info(f"📤 Сигнал отправлен в Telegram: {signal['symbol']} {signal['action']}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сигнала в Telegram: {e}")

async def main():
    """Основная функция"""
    # Конфигурация
    TOKEN = "8243982780:AAHb72Vjf76iIbiS-khO0dLhkmgvsbKKobg"
    CHAT_ID = "5333574230"
    
    # Создаем и запускаем бота
    bot = TelegramEnhancedBot(TOKEN, CHAT_ID)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
        await bot.stop()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main()) 