#!/usr/bin/env python3
"""
Telegram Test Bot - Тестовый Telegram бот для CryptoAlphaPro
"""

import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from universal_crypto_alpha_bot import UniversalCryptoAlphaBot
import yaml

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramTestBot:
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()
        
        # Инициализируем основной бот
        config = {
            'trading': {
                'pairs': [
                    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
                    'DOT/USDT', 'LINK/USDT', 'MATIC/USDT', 'AVAX/USDT', 'ATOM/USDT',
                    'XRP/USDT', 'LTC/USDT', 'BCH/USDT', 'EOS/USDT', 'TRX/USDT',
                    'XLM/USDT', 'VET/USDT', 'THETA/USDT', 'FIL/USDT', 'NEAR/USDT',
                    'ALGO/USDT', 'ICP/USDT', 'FTM/USDT', 'SAND/USDT', 'MANA/USDT',
                    'GALA/USDT', 'AXS/USDT', 'CHZ/USDT', 'HOT/USDT', 'ENJ/USDT',
                    'BAT/USDT', 'ZIL/USDT', 'DASH/USDT', 'XMR/USDT', 'ZEC/USDT',
                    'NEO/USDT', 'QTUM/USDT', 'IOTA/USDT', 'XTZ/USDT', 'HBAR/USDT',
                    'ONE/USDT', 'EGLD/USDT', 'FLOW/USDT', 'KSM/USDT', 'MKR/USDT',
                    'COMP/USDT', 'AAVE/USDT', 'UNI/USDT', 'SUSHI/USDT', 'CRV/USDT',
                    'YFI/USDT', 'SNX/USDT', 'BAL/USDT', 'REN/USDT', 'ZRX/USDT',
                    'BAND/USDT', 'OCEAN/USDT', 'ALPHA/USDT', 'AUDIO/USDT', 'STORJ/USDT',
                    'ANKR/USDT', 'CTSI/USDT', 'AR/USDT', 'RLC/USDT', 'SKL/USDT',
                    'GRT/USDT', '1INCH/USDT', 'LRC/USDT', 'OMG/USDT', 'ZEN/USDT',
                    'RVN/USDT', 'HIVE/USDT', 'STEEM/USDT', 'WAVES/USDT', 'DCR/USDT',
                    'ETC/USDT', 'DOGE/USDT', 'SHIB/USDT', 'M/USDT', 'PEPE/USDT',
                    'FLOKI/USDT', 'BONK/USDT', 'WIF/USDT', 'JUP/USDT', 'PYTH/USDT',
                    'JTO/USDT', 'BOME/USDT', 'SLERF/USDT', 'POPCAT/USDT', 'BOOK/USDT',
                    'MYRO/USDT', 'WEN/USDT', 'CAT/USDT', 'DOG/USDT', 'MOON/USDT',
                    'ROCKET/USDT', 'LAMBO/USDT', 'DIAMOND/USDT', 'GOLD/USDT', 'SILVER/USDT',
                    'PLATINUM/USDT', 'EMERALD/USDT', 'RUBY/USDT', 'SAPPHIRE/USDT', 'OPAL/USDT',
                    'JADE/USDT', 'PEARL/USDT', 'CRYSTAL/USDT', 'GEM/USDT', 'STAR/USDT',
                    'SUN/USDT', 'EARTH/USDT', 'MARS/USDT', 'VENUS/USDT', 'JUPITER/USDT',
                    'SATURN/USDT', 'URANUS/USDT', 'NEPTUNE/USDT', 'PLUTO/USDT', 'MERCURY/USDT',
                    'GALAXY/USDT', 'UNIVERSE/USDT', 'COSMOS/USDT', 'NEBULA/USDT', 'QUASAR/USDT',
                    'PULSAR/USDT', 'BLACKHOLE/USDT', 'WORMHOLE/USDT', 'PORTAL/USDT', 'GATE/USDT',
                    'BRIDGE/USDT', 'TUNNEL/USDT', 'PATH/USDT', 'ROAD/USDT', 'HIGHWAY/USDT',
                    'EXPRESSWAY/USDT', 'AUTOBAHN/USDT', 'FREEWAY/USDT', 'BOULEVARD/USDT', 'AVENUE/USDT',
                    'STREET/USDT', 'LANE/USDT', 'DRIVE/USDT', 'COURT/USDT', 'PLAZA/USDT',
                    'SQUARE/USDT', 'CIRCLE/USDT', 'TRIANGLE/USDT', 'HEART/USDT', 'SPADE/USDT',
                    'CLUB/USDT', 'ACE/USDT', 'KING/USDT', 'QUEEN/USDT', 'JACK/USDT',
                    'JOKER/USDT', 'WILD/USDT', 'BONUS/USDT', 'MEGA/USDT', 'SUPER/USDT',
                    'ULTRA/USDT', 'EXTREME/USDT', 'MAXIMUM/USDT', 'INFINITY/USDT', 'ETERNAL/USDT',
                    'IMMORTAL/USDT', 'LEGENDARY/USDT', 'MYTHICAL/USDT', 'DIVINE/USDT', 'CELESTIAL/USDT',
                    'ANGELIC/USDT', 'DEMONIC/USDT', 'MAGICAL/USDT', 'MYSTICAL/USDT', 'ENCHANTED/USDT',
                    'CURSED/USDT', 'BLESSED/USDT', 'HOLY/USDT', 'SACRED/USDT', 'PROPHETIC/USDT',
                    'ORACULAR/USDT', 'AUGURAL/USDT', 'PREDICTIVE/USDT', 'FORECAST/USDT', 'PROGNOSIS/USDT',
                    'DIAGNOSIS/USDT', 'ANALYSIS/USDT', 'RESEARCH/USDT', 'STUDY/USDT', 'EXAMINATION/USDT',
                    'INVESTIGATION/USDT', 'EXPLORATION/USDT', 'DISCOVERY/USDT', 'INVENTION/USDT', 'INNOVATION/USDT',
                    'CREATION/USDT', 'GENERATION/USDT', 'PRODUCTION/USDT', 'MANUFACTURE/USDT', 'ASSEMBLY/USDT',
                    'CONSTRUCTION/USDT', 'BUILDING/USDT', 'DEVELOPMENT/USDT', 'GROWTH/USDT', 'EXPANSION/USDT',
                    'EXTENSION/USDT', 'ENLARGEMENT/USDT', 'AMPLIFICATION/USDT', 'MAGNIFICATION/USDT', 'INTENSIFICATION/USDT',
                    'ACCELERATION/USDT', 'BOOST/USDT', 'PUSH/USDT', 'DRIVE/USDT', 'PROPEL/USDT',
                    'THRUST/USDT', 'LAUNCH/USDT', 'BLAST/USDT', 'EXPLOSION/USDT', 'DETONATION/USDT',
                    'IGNITION/USDT', 'COMBUSTION/USDT', 'FIRE/USDT', 'FLAME/USDT', 'BLAZE/USDT',
                    'INFERNO/USDT', 'VOLCANO/USDT', 'ERUPTION/USDT', 'TORNADO/USDT', 'HURRICANE/USDT',
                    'CYCLONE/USDT', 'TYPHOON/USDT', 'STORM/USDT', 'THUNDER/USDT', 'LIGHTNING/USDT',
                    'ELECTRICITY/USDT', 'POWER/USDT', 'ENERGY/USDT', 'FORCE/USDT', 'STRENGTH/USDT',
                    'MIGHT/USDT', 'DOMINANCE/USDT', 'SUPREMACY/USDT', 'LEADERSHIP/USDT', 'GUIDANCE/USDT',
                    'DIRECTION/USDT', 'NAVIGATION/USDT', 'PILOTAGE/USDT', 'STEERING/USDT', 'CONTROL/USDT',
                    'MANAGEMENT/USDT', 'ADMINISTRATION/USDT', 'GOVERNANCE/USDT', 'RULERSHIP/USDT', 'SOVEREIGNTY/USDT',
                    'AUTHORITY/USDT', 'JURISDICTION/USDT', 'TERRITORY/USDT', 'DOMAIN/USDT', 'REALM/USDT',
                    'EMPIRE/USDT', 'KINGDOM/USDT', 'PRINCIPALITY/USDT', 'DUCHY/USDT', 'COUNTY/USDT',
                    'PROVINCE/USDT', 'REGION/USDT', 'ZONE/USDT', 'SECTOR/USDT', 'AREA/USDT',
                    'SPACE/USDT', 'DIMENSION/USDT', 'REALITY/USDT', 'EXISTENCE/USDT', 'BEING/USDT',
                    'ENTITY/USDT', 'CREATURE/USDT', 'ORGANISM/USDT', 'LIFE/USDT', 'VITALITY/USDT',
                    'VIGOR/USDT', 'VIBRANCY/USDT', 'DYNAMISM/USDT', 'ACTIVITY/USDT', 'MOVEMENT/USDT',
                    'MOTION/USDT', 'ACTION/USDT', 'OPERATION/USDT', 'FUNCTION/USDT', 'PERFORMANCE/USDT',
                    'EXECUTION/USDT', 'IMPLEMENTATION/USDT', 'DEPLOYMENT/USDT', 'INITIATION/USDT', 'START/USDT',
                    'BEGINNING/USDT', 'COMMENCEMENT/USDT', 'ORIGIN/USDT', 'SOURCE/USDT', 'ROOT/USDT',
                    'FOUNDATION/USDT', 'BASE/USDT', 'GROUND/USDT', 'FLOOR/USDT', 'CEILING/USDT',
                    'ROOF/USDT', 'SKY/USDT', 'HEAVEN/USDT', 'PARADISE/USDT', 'UTOPIA/USDT',
                    'EDEN/USDT', 'GARDEN/USDT', 'FOREST/USDT', 'JUNGLE/USDT', 'SAVANNA/USDT',
                    'DESERT/USDT', 'OCEAN/USDT', 'SEA/USDT', 'LAKE/USDT', 'RIVER/USDT',
                    'STREAM/USDT', 'CREEK/USDT', 'BROOK/USDT', 'SPRING/USDT', 'WELL/USDT',
                    'FOUNTAIN/USDT', 'WATERFALL/USDT', 'CASCADE/USDT', 'RAPIDS/USDT', 'WHIRLPOOL/USDT',
                    'VORTEX/USDT', 'SPIRAL/USDT', 'HELIX/USDT', 'COIL/USDT', 'RING/USDT',
                    'LOOP/USDT', 'CYCLE/USDT', 'ROTATION/USDT', 'REVOLUTION/USDT', 'ORBIT/USDT',
                    'TRAJECTORY/USDT', 'ROUTE/USDT', 'WAY/USDT'
                ],
                'timeframes': ['15m', '1h', '4h', '1d'],
                'update_frequency': 300,
                'min_confidence': 0.6,  # Временно снижено для тестирования
                'top_signals': 10
            },
            'analysis': {
                'min_confidence': 0.6,  # Временно снижено для тестирования
                'min_risk_reward': 2.0,  # Снижено для тестирования
                'max_signals_per_cycle': 10
            }
        }
        
        self.crypto_bot = UniversalCryptoAlphaBot(config)
        self.running = False
        self.trading_task = None
        
        # Настраиваем команды
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Настраивает обработчики команд"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("startbot", self.start_bot))
        self.application.add_handler(CommandHandler("stopbot", self.stop_bot))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("signals", self.signals_command))
        self.application.add_handler(CommandHandler("pairs", self.pairs_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        welcome_text = """
🚀 **CryptoAlphaPro Signal Bot v3.0**

Добро пожаловать! Я - продвинутый AI-бот для генерации торговых сигналов.

**Возможности:**
• Анализ 200+ торговых пар
• Система "Best Alpha Only"
• Детальные объяснения сигналов
• Telegram интеграция

**Команды:**
/startbot - Запустить генерацию сигналов
/stopbot - Остановить бота
/status - Статус работы
/signals - Статистика сигналов
/pairs - Список торговых пар
/help - Справка

**Текущие настройки:**
• Минимальная уверенность: 60% (тестовый режим)
• Топ сигналов: 10
• Обновление: каждые 5 минут
        """
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def start_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запускает торгового бота"""
        if self.running:
            await update.message.reply_text("❌ Бот уже запущен!")
            return
        
        try:
            self.running = True
            self.trading_task = asyncio.create_task(self._trading_loop(update, context))
            await update.message.reply_text("🚀 Бот запущен! Анализирую 200+ пар...")
            logger.info("Telegram бот запущен")
        except Exception as e:
            self.running = False
            await update.message.reply_text(f"❌ Ошибка запуска: {e}")
            logger.error(f"Ошибка запуска бота: {e}")
    
    async def stop_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Останавливает торгового бота"""
        if not self.running:
            await update.message.reply_text("❌ Бот не запущен!")
            return
        
        try:
            self.running = False
            if self.trading_task:
                self.trading_task.cancel()
                self.trading_task = None
            await self.crypto_bot.stop()
            await update.message.reply_text("🛑 Бот остановлен!")
            logger.info("Telegram бот остановлен")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка остановки: {e}")
            logger.error(f"Ошибка остановки бота: {e}")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает статус бота"""
        status = self.crypto_bot.get_status()
        
        status_text = f"""
📊 **Статус бота:**

🔄 **Состояние:** {'🟢 Запущен' if self.running else '🔴 Остановлен'}
📈 **Всего сигналов:** {status['signal_count']}
🔄 **Цикл:** #{status['cycle_count']}
⏰ **Последний сигнал:** {status['last_signal_time_str']}
📊 **Пар:** {status['pairs_count']}
⏱️ **Таймфреймов:** {status['timeframes_count']}
🎯 **Минимальная уверенность:** {status['min_confidence']*100:.0f}%
🎯 **Топ сигналов:** {status['top_signals']}
⏰ **Частота обновления:** {status['update_frequency']} сек
        """
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает статистику сигналов"""
        status = self.crypto_bot.get_status()
        
        signals_text = f"""
📈 **Статистика сигналов:**

🎯 **Всего сигналов:** {status['signal_count']}
⏰ **Последний сигнал:** {status['last_signal_time_str']}
🔄 **Текущий цикл:** #{status['cycle_count']}
📊 **Анализировано пар:** {status['pairs_count']}
🎯 **Топ сигналов:** {status['top_signals']}
⚙️ **Минимальная уверенность:** {status['min_confidence']*100:.0f}%
        """
        
        await update.message.reply_text(signals_text, parse_mode='Markdown')
    
    async def pairs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает список торговых пар"""
        pairs = self.crypto_bot.pairs[:20]  # Показываем первые 20 пар
        
        pairs_text = "📊 **Торговые пары (первые 20):**\n\n"
        for i, pair in enumerate(pairs, 1):
            pairs_text += f"{i}. {pair}\n"
        
        pairs_text += f"\n**Всего пар:** {len(self.crypto_bot.pairs)}"
        
        await update.message.reply_text(pairs_text, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает справку"""
        help_text = """
❓ **Справка по командам:**

🚀 **/startbot** - Запустить генерацию сигналов
🛑 **/stopbot** - Остановить бота
📊 **/status** - Статус работы бота
📈 **/signals** - Статистика сигналов
📋 **/pairs** - Список торговых пар
❓ **/help** - Эта справка

**Как использовать:**
1. Отправьте `/startbot` для запуска
2. Бот будет анализировать 200+ пар каждые 5 минут
3. Топовые сигналы будут отправляться автоматически
4. Используйте `/status` для проверки работы
5. Отправьте `/stopbot` для остановки

**Настройки:**
• Минимальная уверенность: 60% (тестовый режим)
• Топ сигналов: 10
• Обновление: каждые 5 минут
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def _trading_loop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Основной торговый цикл"""
        try:
            while self.running:
                # Получаем топовые сигналы
                top_signals = await self.crypto_bot.ai_engine.process_and_collect_signals(
                    self.crypto_bot.pairs,
                    self.crypto_bot.timeframes,
                    self.crypto_bot.data_manager,
                    min_confidence=self.crypto_bot.min_confidence,
                    top_n=self.crypto_bot.top_signals
                )
                
                # Отправляем сигналы в Telegram
                if top_signals:
                    for signal in top_signals:
                        message = self.crypto_bot._format_signal_message(signal)
                        await update.message.reply_text(message, parse_mode='Markdown')
                        self.crypto_bot.signal_count += 1
                        self.crypto_bot.last_signal_time = asyncio.get_event_loop().time()
                
                # Ждем следующего цикла
                await asyncio.sleep(self.crypto_bot.update_frequency)
                
        except asyncio.CancelledError:
            logger.info("Торговый цикл остановлен")
        except Exception as e:
            logger.error(f"Ошибка в торговом цикле: {e}")
            await update.message.reply_text(f"❌ Ошибка в торговом цикле: {e}")
        finally:
            self.running = False
            self.trading_task = None
    
    async def run(self):
        """Запускает Telegram бота"""
        logger.info("Запуск Telegram бота...")
        await self.application.initialize()
        await self.application.start()
        await self.application.run_polling()

async def main():
    """Основная функция"""
    # Токен бота (замените на свой)
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # Замените на реальный токен
    
    if TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("❌ Пожалуйста, замените TOKEN на реальный токен вашего Telegram бота!")
        return
    
    bot = TelegramTestBot(TOKEN)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main()) 