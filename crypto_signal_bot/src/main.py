#!/usr/bin/env python3
"""
CryptoAlphaPro - Professional Crypto Signal Bot
Main application entry point with AI Engine integration
"""

import asyncio
import signal
import sys
from pathlib import Path
from typing import List
import yaml
from loguru import logger

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config.config_manager import ConfigManager
from src.data_collector.data_manager import DataManager
from src.analytics.signal_generator import SignalGenerator
from src.analytics.realtime_ai_engine import RealtimeAIEngine
from src.risk_management.risk_manager import RiskManager
from src.prediction.ml_predictor import MLPredictor
from src.telegram_bot.bot import TelegramBot
from src.arbitrage.arbitrage_manager import ArbitrageManager
from src.monitoring.prometheus_metrics import PrometheusMetrics


class CryptoAlphaPro:
    """Main application class with AI Engine"""
    
    def __init__(self):
        self.config = None
        self.data_manager = None
        self.signal_generator = None
        self.ai_engine = None  # New AI Engine
        self.risk_manager = None
        self.ml_predictor = None
        self.telegram_bot = None
        self.arbitrage_manager = None
        self.monitoring = None
        self.running = False
        self.tasks: List[asyncio.Task] = []
        
    async def initialize(self):
        """Initialize all components"""
        try:
            logger.info("🚀 Starting CryptoAlphaPro with AI Engine...")
            
            # Load configuration
            self.config = ConfigManager()
            await self.config.load_config()
            logger.info("✅ Configuration loaded")
            
            # Initialize monitoring
            self.monitoring = PrometheusMetrics()
            self.monitoring.start_server()
            logger.info("✅ Monitoring initialized")
            
            # Initialize data manager
            self.data_manager = DataManager(self.config)
            await self.data_manager.initialize()
            logger.info("✅ Data manager initialized")
            
            # Initialize ML predictor
            self.ml_predictor = MLPredictor(self.config)
            await self.ml_predictor.load_models()
            logger.info("✅ ML models loaded")
            
            # Initialize risk manager
            self.risk_manager = RiskManager(self.config)
            logger.info("✅ Risk manager initialized")
            
            # Initialize AI Engine (NEW)
            self.ai_engine = RealtimeAIEngine(
                config=self.config,
                data_manager=self.data_manager,
                risk_manager=self.risk_manager
            )
            logger.info("✅ AI Engine initialized")
            
            # Initialize signal generator
            self.signal_generator = SignalGenerator(
                config=self.config,
                data_manager=self.data_manager,
                ml_predictor=self.ml_predictor
            )
            logger.info("✅ Signal generator initialized")
            
            # Initialize arbitrage manager
            self.arbitrage_manager = ArbitrageManager(
                config=self.config,
                data_manager=self.data_manager
            )
            logger.info("✅ Arbitrage manager initialized")
            
            # Initialize Telegram bot
            self.telegram_bot = TelegramBot(self.config)
            await self.telegram_bot.initialize()
            logger.info("✅ Telegram bot initialized")
            
            # Connect AI Engine to data streams
            await self._setup_ai_data_streams()
            
            logger.success("🎉 All components initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize: {e}")
            raise
    
    async def _setup_ai_data_streams(self):
        """Setup AI Engine data stream connections"""
        try:
            # Hook into data manager's WebSocket streams
            if hasattr(self.data_manager, '_handle_websocket_message'):
                original_handler = self.data_manager._handle_websocket_message
                
                async def enhanced_handler(exchange: str, message: dict):
                    # Call original handler
                    await original_handler(exchange, message)
                    
                    # Feed data to AI Engine
                    if message.get('type') == 'ticker' and 'data' in message:
                        ticker = message['data']
                        await self.ai_engine.process_tick(
                            exchange=exchange,
                            symbol=ticker.get('symbol', ''),
                            price=ticker.get('last', 0),
                            volume=ticker.get('baseVolume', 0),
                            timestamp=ticker.get('timestamp')
                        )
                    elif message.get('type') == 'trade' and 'data' in message:
                        for trade in message['data']:
                            await self.ai_engine.process_tick(
                                exchange=exchange,
                                symbol=trade.get('symbol', ''),
                                price=trade.get('price', 0),
                                volume=trade.get('amount', 0),
                                timestamp=trade.get('timestamp')
                            )
                
                # Replace handler
                self.data_manager._handle_websocket_message = enhanced_handler
                
            logger.info("✅ AI Engine connected to data streams")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup AI data streams: {e}")
    
    async def start_background_tasks(self):
        """Start all background tasks"""
        try:
            # Data collection task
            data_task = asyncio.create_task(
                self.data_manager.start_data_collection(),
                name="data_collection"
            )
            self.tasks.append(data_task)
            
            # AI Engine task (NEW - highest priority)
            ai_engine_task = asyncio.create_task(
                self.ai_engine.start(),
                name="ai_engine"
            )
            self.tasks.append(ai_engine_task)
            
            # Signal generation task
            signal_task = asyncio.create_task(
                self.signal_generator.start_signal_generation(),
                name="signal_generation"
            )
            self.tasks.append(signal_task)
            
            # Arbitrage monitoring task
            arbitrage_task = asyncio.create_task(
                self.arbitrage_manager.start_monitoring(),
                name="arbitrage_monitoring"
            )
            self.tasks.append(arbitrage_task)
            
            # Telegram bot task
            bot_task = asyncio.create_task(
                self.telegram_bot.start(),
                name="telegram_bot"
            )
            self.tasks.append(bot_task)
            
            # Model retraining task (daily)
            retrain_task = asyncio.create_task(
                self.schedule_daily_retraining(),
                name="model_retraining"
            )
            self.tasks.append(retrain_task)
            
            # Health monitoring task  
            health_task = asyncio.create_task(
                self.monitor_system_health(),
                name="health_monitoring"
            )
            self.tasks.append(health_task)
            
            # Performance monitoring task (NEW)
            perf_task = asyncio.create_task(
                self.monitor_ai_performance(),
                name="ai_performance_monitoring"
            )
            self.tasks.append(perf_task)
            
            # News feed task (NEW)
            news_task = asyncio.create_task(
                self.process_news_feed(),
                name="news_processing"
            )
            self.tasks.append(news_task)
            
            logger.info(f"✅ Started {len(self.tasks)} background tasks")
            
        except Exception as e:
            logger.error(f"❌ Failed to start background tasks: {e}")
            raise
    
    async def schedule_daily_retraining(self):
        """Schedule daily model retraining"""
        while self.running:
            try:
                # Wait 24 hours
                await asyncio.sleep(24 * 60 * 60)
                
                if self.running:
                    logger.info("🔄 Starting daily model retraining...")
                    await self.ml_predictor.retrain_models()
                    logger.success("✅ Model retraining completed")
                    
            except Exception as e:
                logger.error(f"❌ Error in model retraining: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retry
    
    async def monitor_system_health(self):
        """Monitor system health and send alerts"""
        while self.running:
            try:
                # Check system health every 5 minutes
                await asyncio.sleep(300)
                
                if self.running:
                    health_status = await self.check_system_health()
                    
                    if not health_status['healthy']:
                        alert_message = self.format_health_alert(health_status)
                        await self.telegram_bot.send_alert(alert_message)
                        
            except Exception as e:
                logger.error(f"❌ Error in health monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def monitor_ai_performance(self):
        """Monitor AI Engine performance"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                if self.running and self.ai_engine:
                    stats = self.ai_engine.get_performance_stats()
                    
                    if stats:
                        # Update Prometheus metrics
                        if self.monitoring:
                            self.monitoring.record_model_prediction(
                                'ai_engine', 
                                'real_time',
                            )
                            
                        # Log performance
                        avg_time = stats.get('avg_processing_time_ms', 0)
                        if avg_time > 0:
                            logger.info(f"🔬 AI Engine: {avg_time:.2f}ms avg, "
                                      f"{stats.get('signals_generated', 0)} signals generated")
                            
                            # Alert if performance degrades
                            if avg_time > 10:  # Over 10ms average
                                await self.telegram_bot.send_alert(
                                    f"⚠️ AI Engine performance degraded: {avg_time:.2f}ms average"
                                )
                        
            except Exception as e:
                logger.error(f"❌ Error in AI performance monitoring: {e}")
                await asyncio.sleep(60)
    
    async def process_news_feed(self):
        """Process news feed for AI Engine"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                if self.running and self.data_manager.news_collector:
                    # Get latest news
                    news_data = await self.data_manager.news_collector.get_crypto_news()
                    
                    if news_data and self.ai_engine:
                        # Feed to AI Engine
                        await self.ai_engine.process_news(news_data)
                        
            except Exception as e:
                logger.error(f"❌ Error in news processing: {e}")
                await asyncio.sleep(60)
    
    async def check_system_health(self) -> dict:
        """Check system health"""
        health_status = {
            'healthy': True,
            'issues': []
        }
        
        try:
            # Check data collection
            if not self.data_manager.is_healthy():
                health_status['healthy'] = False
                health_status['issues'].append("Data collection issues detected")
            
            # Check database connections
            db_health = await self.data_manager.check_database_health()
            if not db_health:
                health_status['healthy'] = False
                health_status['issues'].append("Database connection issues")
            
            # Check exchange connections
            exchange_health = await self.data_manager.check_exchange_health()
            if not exchange_health:
                health_status['healthy'] = False
                health_status['issues'].append("Exchange connection issues")
            
            # Check model performance
            model_health = self.ml_predictor.check_model_health()
            if not model_health:
                health_status['healthy'] = False
                health_status['issues'].append("ML model performance degradation")
            
            # Check AI Engine performance (NEW)
            if self.ai_engine:
                ai_stats = self.ai_engine.get_performance_stats()
                if ai_stats.get('avg_processing_time_ms', 0) > 50:  # Over 50ms
                    health_status['healthy'] = False
                    health_status['issues'].append("AI Engine performance degraded")
                
        except Exception as e:
            health_status['healthy'] = False
            health_status['issues'].append(f"Health check error: {str(e)}")
        
        return health_status
    
    def format_health_alert(self, health_status: dict) -> str:
        """Format health alert message"""
        message = "🚨 SYSTEM HEALTH ALERT\n\n"
        message += "Issues detected:\n"
        
        for issue in health_status['issues']:
            message += f"• {issue}\n"
        
        message += "\nPlease check system logs for more details."
        return message
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down CryptoAlphaPro...")
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Shutdown components
        if self.ai_engine:
            await self.ai_engine.shutdown()
        
        if self.telegram_bot:
            await self.telegram_bot.shutdown()
        
        if self.data_manager:
            await self.data_manager.shutdown()
        
        if self.arbitrage_manager:
            await self.arbitrage_manager.shutdown()
        
        logger.success("✅ Shutdown completed")
    
    async def run(self):
        """Main run method"""
        try:
            # Initialize components
            await self.initialize()
            
            # Set running flag
            self.running = True
            
            # Start background tasks
            await self.start_background_tasks()
            
            logger.success("🎯 CryptoAlphaPro with AI Engine is running! Press Ctrl+C to stop.")
            
            # Wait for all tasks to complete
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ Critical error: {e}")
            raise
        finally:
            await self.shutdown()


def setup_signal_handlers(app: CryptoAlphaPro):
    """Setup signal handlers for graceful shutdown"""
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(app.shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point"""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/crypto_alpha_pro.log",
        rotation="1 day",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG"
    )
    
    # Add AI Engine specific logging
    logger.add(
        "logs/ai_engine.log",
        rotation="6 hours",
        retention="7 days",  # Keep AI logs for shorter period due to high volume
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        filter=lambda record: "ai_engine" in record["name"].lower() or "realtime" in record["name"].lower()
    )
    
    app = CryptoAlphaPro()
    setup_signal_handlers(app)
    
    try:
        await app.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 