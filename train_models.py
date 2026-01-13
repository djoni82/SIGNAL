# train_models.py
"""
Standalone script для обучения ML моделей.
Запуск: python train_models.py
"""
import asyncio
import sys
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Добавляем корневую директорию в path
sys.path.insert(0, str(Path(__file__).parent))

from src.strategies.data_pipeline import TradingDataPipeline
from src.core.settings import settings

async def main():
    print("=" * 60)
    print("  SignalPro Ultra - Model Training Pipeline")
    print("=" * 60)
    print()
    
    try:
        pipeline = TradingDataPipeline()
        
        # Символы для обучения (можно кастомизировать)
        training_symbols = [
            'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT',
            'BNB/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOT/USDT',
            'LINK/USDT', 'UNI/USDT', 'MATIC/USDT', 'ATOM/USDT'
        ]
        
        logger.info(f"📊 Training on {len(training_symbols)} symbols")
        logger.info(f"📅 Lookback period: 180 days")
        print()
        
        # 1. Сбор данных
        logger.info("Step 1/2: Collecting historical data...")
        X_train, y_train, X_val, y_val = await pipeline.collect_training_data(
            symbols=training_symbols,
            lookback_days=180
        )
        
        if len(X_train) < 100:
            logger.error("❌ Insufficient data collected!")
            logger.error("   Check: 1) Exchange API limits, 2) Network connection")
            sys.exit(1)
        
        logger.info(f"✅ Data collected: {len(X_train)} training, {len(X_val)} validation samples")
        logger.info(f"   Positive rate: {y_train.mean()*100:.1f}%")
        print()
        
        # 2. Обучение моделей
        logger.info("Step 2/2: Training ensemble models...")
        logger.info("   This may take 10-30 minutes...")
        
        pipeline.ml_engine.train_models(X_train, y_train, X_val, y_val)
        
        print()
        print("=" * 60)
        logger.info("✅ Training complete!")
        logger.info(f"   Models saved to: models/")
        logger.info(f"   - xgb_model.json")
        logger.info(f"   - lgbm_model.txt")
        logger.info(f"   - catboost_model.cbm")
        logger.info(f"   - features.pkl")
        print()
        logger.info("🚀 Next steps:")
        logger.info("   1. Set USE_ULTRA_MODE=true in settings.py")
        logger.info("   2. Restart the bot: python main.py")
        logger.info("   3. Setup auto-retraining: ./setup_auto_retraining.sh")
        print("=" * 60)
        
    except KeyboardInterrupt:
        logger.warning("⚠️  Training interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"❌ Training failed: {e}")
        logger.error("   Check logs above for details")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
