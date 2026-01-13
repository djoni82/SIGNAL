# src/strategies/data_pipeline.py
"""
Trading Data Pipeline - сбор данных и обучение ML моделей.
Запускается отдельно от основного бота (по расписанию или вручную).
"""
import ccxt
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
import logging
import sys

# Добавляем корневую директорию в path для импортов
sys.path.insert(0, '/Users/zhakhongirkuliboev/SIGNAL')

from src.strategies.advanced_features import AdvancedFeatureEngineer
from src.strategies.smart_money_analyzer import SmartMoneyAnalyzer
from src.strategies.ml_engine_real import RealMLEngine
from src.strategies.adaptive_indicators import ImprovedAdaptiveIndicatorEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingDataPipeline:
    """
    Пайплайн для сбора исторических данных и обучения ML моделей.
    """
    def __init__(self):
        # Use Binance Futures for funding rates and OI
        from src.core.settings import settings
        self.exchange = ccxt.binance({
            'apiKey': settings.binance_key if settings.binance_key != 'ВАШ_BINANCE_API_KEY' else None,
            'secret': settings.binance_secret if settings.binance_secret != 'ВАШ_BINANCE_SECRET' else None,
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })
        self.feature_engineer = AdvancedFeatureEngineer()
        self.indicator_engine = ImprovedAdaptiveIndicatorEngine()
        self.ml_engine = RealMLEngine()
        
    async def collect_training_data(self, symbols: list, lookback_days=180):
        """
        Собирает данные для обучения.
        
        X (Features): TA индикаторы + Advanced features
        y (Target): 1 если цена выросла > 2% за следующие 4 часа, иначе 0
        """
        all_features = []
        all_labels = []
        
        logger.info(f"📊 Collecting data for {len(symbols)} symbols, {lookback_days} days history...")
        
        for symbol in symbols:
            try:
                logger.info(f"Fetching {symbol}...")
                
                # Загружаем OHLCV данные
                since = self.exchange.parse8601(
                    (datetime.now() - timedelta(days=lookback_days)).isoformat()
                )
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol, 
                    timeframe='1h', 
                    since=since, 
                    limit=1000  # CCXT limit usually 500-1000
                )
                
                if len(ohlcv) < 100:
                    logger.warning(f"Not enough data for {symbol}")
                    continue
                
                # Создаем DataFrame
                df = pd.DataFrame(
                    ohlcv, 
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                # === СБОР СМАРТ-МАНИ ДАННЫХ ===
                # 1. Historical Funding Rates
                # fapiPublicGetFundingRate возвращает до 1000 записей
                raw_symbol = symbol.replace('/', '').replace(':', '')
                funding_history = self.exchange.fapiPublicGetFundingRate({
                    'symbol': raw_symbol,
                    'limit': 1000
                })
                
                # Создаем маппинг времени к ставке
                funding_map = {
                    pd.to_datetime(int(x['fundingTime']), unit='ms').floor('1h'): float(x['fundingRate'])
                    for x in funding_history
                }
                
                # === ГЕНЕРАЦИЯ ФИЧЕЙ ===
                
                # === ГЕНЕРАЦИЯ ФИЧЕЙ ===
                
                # 1. Advanced Features (Hurst, DFA, Entropy)
                adv_features = self.feature_engineer.create_advanced_features(df)
                
                # 2. Technical Indicators (Match UltraSignalGenerator)
                df['rsi'] = self.indicator_engine._calculate_rsi(df['close'])
                df['adx'] = self.indicator_engine._calculate_adx(df)
                df['atr'] = self.indicator_engine._calculate_atr_direct(df) # Need this helper
                
                # Объединяем все фичи в один словарь для каждой строки
                feature_rows = []
                for idx in range(100, len(df)):
                    close_price = df['close'].iloc[idx]
                    ts_floor = df.index[idx].floor('1h')
                    
                    # Получаем все адванс фичи для этой строки
                    # (Для обучения на истории берем под-фрейм до текущего момента)
                    current_adv = self.feature_engineer.create_advanced_features(df.iloc[:idx+1])
                    
                    row_features = {
                        **current_adv,
                        'rsi': df['rsi'].iloc[idx] if pd.notna(df['rsi'].iloc[idx]) else 50.0,
                        'atr': df['atr'].iloc[idx] / close_price if pd.notna(df['atr'].iloc[idx]) else 0.01,
                        'adx': df['adx'].iloc[idx] if pd.notna(df['adx'].iloc[idx]) else 20.0,
                        'sma_20': (df['close'].rolling(20).mean().iloc[idx] / close_price),
                        'sma_50': (df['close'].rolling(50).mean().iloc[idx] / close_price),
                        'volume_ratio': (df['volume'].iloc[idx] / df['volume'].rolling(20).mean().iloc[idx]),
                        'funding_rate': funding_map.get(ts_floor, 0.0),
                        'liq_ratio': 1.0
                    }
                    feature_rows.append(row_features)
                
                features_df = pd.DataFrame(feature_rows)
                # Устанавливаем индекс из оригинального DF со сдвигом 100
                features_df.index = df.index[100:]
                
                # === ГЕНЕРАЦИЯ ТАРГЕТА (LABEL) ===
                # y = 1 если цена вырастет > 1.5% за следующие 4 часа
                # Выравниваем таргет с индексами фич
                df_slice = df.iloc[100:]
                future_returns = (df['close'].shift(-4) / df['close']).iloc[100:] - 1
                labels = (future_returns > 0.015).astype(int)
                
                # Убираем последние строки без таргета (где shift-4 дал NaN)
                valid_mask = future_returns.notna()
                features_df = features_df[valid_mask]
                labels = labels[valid_mask]
                
                all_features.append(features_df)
                all_labels.append(labels)
                
                logger.info(f"✅ {symbol}: {len(features_df)} samples")
                
            except Exception as e:
                logger.error(f"❌ Error collecting {symbol}: {e}")
                
        if not all_features:
            raise ValueError("No data collected. Check symbols or exchange connectivity.")
        
        # Объединяем все данные
        X = pd.concat(all_features, ignore_index=True)
        y = pd.concat(all_labels, ignore_index=True)
        
        # Train/Val split (80/20)
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, 
            test_size=0.2, 
            shuffle=False,  # Сохраняем временной порядок
            random_state=42
        )
        
        logger.info(f"📊 Data split: Train={len(X_train)}, Val={len(X_val)}")
        logger.info(f"   Positive samples (profit): {y_train.sum()} / {len(y_train)} ({y_train.mean()*100:.1f}%)")
        
        return X_train, y_train, X_val, y_val

    def _calculate_simple_rsi(self, prices, period=14):
        """Упрощенный RSI для фичей"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = -delta.where(delta < 0, 0).rolling(period).mean()
        rs = gain / loss.replace(0, 1e-10)
        return 100 - (100 / (1 + rs))

    def _calculate_simple_atr(self, df, period=14):
        """Упрощенный ATR для фичей"""
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    async def train_loop(self, symbols=None):
        """
        Главная функция: собирает данные и обучает модели.
        """
        if symbols is None:
            # Default: топ ликвидные пары
            symbols = [
                'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT',
                'BNB/USDT', 'ADA/USDT', 'DOGE/USDT', 'AVAX/USDT'
            ]
        
        logger.info("🎓 Starting Training Pipeline...")
        
        try:
            # 1. Collect data
            X_train, y_train, X_val, y_val = await self.collect_training_data(symbols)
            
            # 2. Train models
            self.ml_engine.train_models(X_train, y_train, X_val, y_val)
            
            logger.info("✅ Training Complete! Models saved to models/")
            logger.info("🚀 You can now use Ultra Mode in the main bot")
            
        except Exception as e:
            logger.error(f"❌ Training failed: {e}")
            raise
        finally:
            await self.exchange.close()

async def main():
    """Точка входа для standalone запуска"""
    pipeline = TradingDataPipeline()
    await pipeline.train_loop()

if __name__ == "__main__":
    asyncio.run(main())
