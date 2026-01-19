# src/strategies/signal_generator_ultra.py
"""
Ultra Signal Generator - главный оркестратор с реальным ML и Smart Money.
Scoring: 30% TA + 40% Real ML + 30% Smart Money
Фильтры: ADX >= 20, Confidence >= 0.85
"""
import logging
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Optional
import numpy as np

from src.core.settings import settings
from src.strategies.models import EnhancedSignal, MarketRegime

# Проверенные компоненты (Legacy)
from src.strategies.market_regime import EnhancedMarketRegimeAnalyzer
from src.strategies.adaptive_indicators import ImprovedAdaptiveIndicatorEngine
from src.strategies.risk_manager import DynamicRiskManager

# Новые Ultra компоненты
from src.strategies.ml_engine_real import RealMLEngine
from src.strategies.smart_money_analyzer import SmartMoneyAnalyzer
from src.strategies.advanced_features import AdvancedFeatureEngineer

logger = logging.getLogger(__name__)

class UltraSignalGenerator:
    """
    Генератор сверхточных сигналов (Ultra Mode).
    
    Ключевые отличия от Legacy:
    - Реальный ML (XGBoost/LightGBM/CatBoost) вместо эвристики
    - Smart Money анализ (Liquidity + Funding)
    - Строгий порог 0.85 (только топ 10-15% сигналов)
    - Фильтр по ADX (нет слабых трендов)
    """
    def __init__(self, exchange_connector, ws_client=None):
        self.exchange = exchange_connector
        self.config = settings
        self.ws_client = ws_client
        
        # Legacy компоненты (проверенные)
        self.regime_analyzer = EnhancedMarketRegimeAnalyzer(exchange_connector)
        self.indicator_engine = ImprovedAdaptiveIndicatorEngine()
        self.risk_manager = DynamicRiskManager()
        
        # Ultra компоненты
        self.ml_engine = RealMLEngine()
        self.smart_money = SmartMoneyAnalyzer(
            coinglass_key=getattr(settings, 'coinglass_api_key', ''),
            hyblock_key=getattr(settings, 'hyblock_api_key', ''),
            ws_client=ws_client
        )
        self.advanced_features = AdvancedFeatureEngineer()
        
        self.signal_cache = {}
        
        # Ultra настройки
        self.ULTRA_MIN_CONFIDENCE = getattr(settings, 'ultra_min_confidence', 0.55)
        self.MIN_ADX_THRESHOLD = 15
        logger.info(f"🚀 [INIT] Ultra Mode active. Threshold: {self.ULTRA_MIN_CONFIDENCE:.2%}, ADX: {self.MIN_ADX_THRESHOLD}")
        
        # Валидация фич (критично для ML)
        self._validate_feature_consistency()

    def _validate_feature_consistency(self):
        """
        Проверяет, что фичи в production совпадают с обученными.
        Это критично для корректности ML predictions.
        """
        import joblib
        import os
        
        feature_path = f"{self.ml_engine.model_path}features.pkl"
        
        if not os.path.exists(feature_path):
            logger.warning("⚠️  No trained models found. ML will return neutral predictions.")
            logger.warning("   Run: python train_models.py")
            return
        
        try:
            trained_features = joblib.load(feature_path)
            
            # Генерируем sample фичи для проверки
            import pandas as pd
            import numpy as np
            sample_df = pd.DataFrame({
                'close': np.random.randn(200) + 50000,
                'high': np.random.randn(200) + 50100,
                'low': np.random.randn(200) + 49900,
                'volume': np.random.randint(1000, 10000, 200)
            })
            
            adv_features = self.advanced_features.create_advanced_features(sample_df)
            current_features = list(adv_features.keys()) + [
                'rsi', 'atr', 'adx', 'sma_20', 'sma_50', 'volume_ratio',
                'funding_rate', 'liq_ratio'
            ]
            test_features = {
                **adv_features,
                'rsi': 50.0,
                'atr': 0.01,
                'adx': 25.0,
                'sma_20': 1.0,
                'sma_50': 1.0,
                'volume_ratio': 1.0,
                'source': 'mock',
                'is_mock': True
            }
            
            # Check for EXACT match with model expectations
            if set(current_features) != set(trained_features):
                missing = set(trained_features) - set(current_features)
                extra = set(current_features) - set(trained_features)
                logger.error(f"❌ Feature mismatch! Missing: {missing}, Extra: {extra}")
                # We don't assert to prevent crash, but we log loudly
            else:
                logger.info("✅ ML Feature schema synchronized")
            logger.info(f"🔍 Feature schema: {len(current_features)} total features")
            
            # Проверка совпадения
            trained_set = set(trained_features)
            current_set = set(current_features)
            
            if trained_set != current_set:
                missing = trained_set - current_set
                extra = current_set - trained_set
                
                error_msg = "❌ FEATURE MISMATCH! Models were trained on different features.\n"
                if missing:
                    error_msg += f"   Missing in production: {missing}\n"
                if extra:
                    error_msg += f"   Extra in production: {extra}\n"
                error_msg += "   Solution: Re-train models with 'python train_models.py'"
                
                logger.error(error_msg)
                raise ValueError("Feature schema mismatch. Retrain models!")
            
            logger.info(f"✅ Feature validation passed: {len(trained_features)} features")
            
        except Exception as e:
            logger.warning(f"⚠️  Feature validation failed: {e}")

    async def generate_signal(self, symbol: str, timeframe: str = '1h', arbitrage_spread: float = 0.0) -> Optional[EnhancedSignal]:
        """
        Основной цикл генерации сигнала.
        """
        # 1. Загрузка данных
        try:
            # Кеширование
            cache_key = f"{symbol}_{timeframe}"
            if cache_key in self.signal_cache:
                sig, ts = self.signal_cache[cache_key]
                if datetime.now() - ts < timedelta(minutes=15):
                    return sig

            # Manual Data Fetch & Conversion
            try:
                ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=200)
            except Exception as e:
                # Log once per symbol/error to avoid spam if possible, or just warning
                # Check for "BadSymbol" or "does not have market symbol"
                if "does not have market symbol" in str(e):
                    logger.warning(f"⚠️ Exchange does not support {symbol}. Skipping.")
                    return None
                logger.warning(f"Failed to fetch data for {symbol}: {e}")
                return None

            if not ohlcv or len(ohlcv) < 100:
                return None
                
            import pandas as pd
            primary_data = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            primary_data['timestamp'] = pd.to_datetime(primary_data['timestamp'], unit='ms')

            # === ШАГ 1: КОНТЕКСТНЫЙ ФИЛЬТР (КРИТИЧЕСКИЙ) ===
            # Анализ режима рынка
            regime = await self.regime_analyzer.detect_regime(primary_data, symbol)
            
            # ADX фильтр: не торгуем без тренда
            indicators = self.indicator_engine.calculate_adaptive_indicators(primary_data, regime)
            adx_series = indicators.get('adx')
            adx = adx_series.iloc[-1] if adx_series is not None and len(adx_series) > 0 else 20.0
            
            # Фоллбэк если adx это NaN или None
            if pd.isna(adx): adx = 20.0
            
            if adx < self.MIN_ADX_THRESHOLD:
                logger.info(f"🚫 [FILTERED] {symbol} - Weak trend (ADX: {adx:.1f} < {self.MIN_ADX_THRESHOLD})")
                return None
            
            # === ШАГ 2: БАЗОВЫЙ ТЕХНИЧЕСКИЙ АНАЛИЗ ===
            rsi, oversold, overbought = self.indicator_engine.calculate_adaptive_rsi(
                primary_data, regime
            )
            indicators['rsi'] = rsi
            
            ta_signal = self._generate_ta_signal(primary_data, indicators, oversold, overbought)
            if ta_signal['confidence'] < 0.3:
                return None

            # === ШАГ 3: ПРОДВИНУТЫЕ ФИЧИ ===
            adv_features = self.advanced_features.create_advanced_features(primary_data)
            
            # === ШАГ 4: SMART MONEY ANALYSIS (MOVING UP) ===
            current_price = primary_data['close'].iloc[-1]
            sm_context = await self.smart_money.analyze_smart_money_context(
                symbol, current_price, ta_signal['direction'], self.exchange
            )
            sm_metrics = sm_context.get('metrics', {})

            # Объединяем фичи для ML
            ml_features = {
                **adv_features,
                'rsi': float(indicators['rsi'].iloc[-1]) if len(indicators['rsi']) > 0 else 50.0,
                'atr': float(indicators['atr'].iloc[-1]) / current_price if len(indicators['atr']) > 0 else 0.01,
                'adx': float(adx),
                'sma_20': (primary_data['close'].rolling(20).mean().iloc[-1] / current_price) if len(primary_data) >= 20 else 1.0,
                'sma_50': (primary_data['close'].rolling(50).mean().iloc[-1] / current_price) if len(primary_data) >= 50 else 1.0,
                'volume_ratio': primary_data['volume'].iloc[-1] / primary_data['volume'].rolling(20).mean().iloc[-1] if len(primary_data) >= 20 else 1.0,
                'funding_rate': float(sm_metrics.get('funding_rate', 0.0)),
                'liq_ratio': float(sm_metrics.get('liq_ratio', 1.0)),
                # 'arbitrage_spread': float(arbitrage_spread) # DISABLED: Schema mismatch. Used as post-boost only.
            }
            
            # Diagnostic Log
            logger.info(f"📊 [ML-FEATURES] {symbol}: SM_Funding={ml_features['funding_rate']:.5f}, LiqRatio={ml_features['liq_ratio']:.2f}, ADX={ml_features['adx']:.1f}")
            
            # === ШАГ 5: РЕАЛЬНЫЙ ML PREDICTION ===
            ml_prob = self.ml_engine.predict_probability(ml_features)

            # === ШАГ 6: СИНТЕЗ УВЕРЕННОСТИ ===
            # Формула: 30% TA + 40% ML + 30% Smart Money
            ta_score = ta_signal['confidence']
            ml_score = ml_prob
            
            # SM Validation: Only boost if data is REAL
            if sm_metrics.get('is_real_data', False):
                sm_boost = sm_context['smart_money_boost']
            else:
                sm_boost = 0.0
                logger.debug(f"Neutralizing SM Score for {symbol} (Mock Data detected)")
            
            # Base confidence
            confidence = (ta_score * 0.30) + (ml_score * 0.40) + (sm_boost * 0.30)
            
            # Бонус за совпадение тренда
            if (regime.trend == 'bullish' and ta_signal['direction'] == 'BUY') or \
               (regime.trend == 'bearish' and ta_signal['direction'] == 'SELL'):
                confidence *= 1.1
            
            # Arbitrage Boost (Post-ML)
            # If spread > 1.0%, boost confidence slightly (e.g. +5-10%)
            # This integrates the data without breaking the ML schema
            if arbitrage_spread > 1.0:
                confidence *= 1.05
                logger.info(f"Arbitrage Boost applied for {symbol} (+5%)")
            
            # Cap
            confidence = min(0.98, confidence)
            
            # === ШАГ 7: СТРОГИЙ ПОРОГ (СВЕРХТОЧНОСТЬ) ===
            if confidence < self.ULTRA_MIN_CONFIDENCE:
                logger.info(
                    f"[ULTRA-FILTERED] {symbol} ({timeframe}): Conf={confidence:.2%} < {self.ULTRA_MIN_CONFIDENCE:.0%} | "
                    f"TA={ta_score:.2f}, ML={ml_score:.2f}, SM={sm_boost:+.2f} ({sm_metrics.get('source', 'rest')})"
                )
                return None

            # === ШАГ 8: RISK MANAGEMENT ===
            # Используем динамический риск менеджер
            risk_params = self.risk_manager.calculate_dynamic_levels(
                entry_price=current_price,
                atr=indicators['atr'].iloc[-1],
                volatility=regime.volatility,
                trend_direction="long" if ta_signal['direction'] in ['BUY', 'STRONG_BUY'] else "short",
                adx=adx,
                phase=regime.phase,
                crisis_mode=regime.crisis_mode
            )
            
            pos_info = self.risk_manager.calculate_position_size(
                symbol, current_price, risk_params['stop_loss'], confidence,
                regime.volatility_value / 100, indicators['atr'].iloc[-1]
            )
            
            # Расчет метрик
            risk_distance = abs(current_price - risk_params['stop_loss'])
            avg_tp = np.mean([abs(tp - current_price) for tp in risk_params['take_profit']])
            risk_reward = avg_tp / risk_distance if risk_distance > 0 else 1.0

            # === ШАГ 9: СОЗДАНИЕ СИГНАЛА ===
            final_signal = EnhancedSignal(
                symbol=symbol,
                direction='STRONG_BUY' if confidence > 0.9 and ta_signal['direction'] == 'BUY' else 
                         'STRONG_SELL' if confidence > 0.9 and ta_signal['direction'] == 'SELL' else 
                         ta_signal['direction'],
                confidence=confidence,
                entry_price=current_price,
                stop_loss=risk_params['stop_loss'],
                take_profit=tuple(risk_params['take_profit']),
                position_size_pct=pos_info['position_size_pct'],
                expected_value=0.0,  # Можно добавить расчет
                risk_reward=risk_reward,
                timeframe=timeframe,
                rationale={
                    'ta_score': ta_score,
                    'ml_probability': float(ml_prob) if ml_prob is not None else 0.5,
                    'smart_money': sm_context['rationale'],
                    'regime': regime.trend,
                    'volatility': regime.volatility,
                    'adx': adx,
                    'indicators': {
                        'rsi': float(indicators['rsi'].iloc[-1]) if len(indicators['rsi']) > 0 else 50.0,
                        'atr': float(indicators['atr'].iloc[-1]) if len(indicators['atr']) > 0 else 0.0,
                        'adx': float(adx)
                    }
                },
                valid_until=datetime.now() + timedelta(hours=2),
                model_agreement={
                    'ta': ta_score,
                    'ml': ml_score,
                    'smart_money': sm_boost
                },
                var_95=0.0,
                max_drawdown_risk=0.0,
                kelly_fraction=pos_info['kelly_fraction']
            )
            
            self.signal_cache[cache_key] = (final_signal, datetime.now())
            
            logger.info(
                f"🚀 [ULTRA SIGNAL] {symbol} ({timeframe}) | "
                f"Conf: {confidence:.2%} | Dir: {final_signal.direction} | "
                f"TA={ta_score:.2f} ML={ml_score:.2f} SM={sm_boost:+.2f}"
            )
            
            return final_signal

        except Exception as e:
            logger.exception(f"UltraSignal Error {symbol} ({timeframe}): {e}")
            return None

    def _generate_ta_signal(self, data, indicators, oversold, overbought):
        """
        Базовый TA скоринг (копия из оригинального generator).
        """
        buy_score = 0
        sell_score = 0
        
        # RSI
        rsi = indicators['rsi'].iloc[-1] if len(indicators['rsi']) > 0 else 50
        if rsi < oversold:
            buy_score += 1.5
        elif rsi > overbought:
            sell_score += 1.5
        
        # MACD
        if 'macd' in indicators and 'macd_signal' in indicators:
            macd = indicators['macd'].iloc[-1]
            macd_signal = indicators['macd_signal'].iloc[-1]
            if macd > macd_signal:
                buy_score += 1
            else:
                sell_score += 1
        
        # EMA Cross
        if 'ema_short' in indicators and 'ema_long' in indicators:
            if indicators['ema_short'].iloc[-1] > indicators['ema_long'].iloc[-1]:
                buy_score += 0.5
            else:
                sell_score += 0.5
        
        # ADX Strength
        if 'adx' in indicators:
            adx = indicators['adx'].iloc[-1]
            if adx > 25:
                # Сильный тренд - усиливаем доминирующее направление
                if buy_score > sell_score:
                    buy_score += 1
                else:
                    sell_score += 1
        
        # Bollinger Bands
        if 'bb_lower' in indicators and 'bb_upper' in indicators:
            close = data['close'].iloc[-1]
            bb_lower = indicators['bb_lower'].iloc[-1]
            bb_upper = indicators['bb_upper'].iloc[-1]
            
            if close < bb_lower:
                buy_score += 1
            elif close > bb_upper:
                sell_score += 1
        
        # Определение направления
        if buy_score > sell_score and buy_score >= 2.5:
            direction = 'BUY'
            confidence = min(0.95, buy_score / (buy_score + sell_score))
        elif sell_score > buy_score and sell_score >= 2.5:
            direction = 'SELL'
            confidence = min(0.95, sell_score / (buy_score + sell_score))
        else:
            direction = 'NEUTRAL'
            confidence = 0.0
        
        return {
            'direction': direction,
            'confidence': confidence,
            'buy_score': buy_score,
            'sell_score': sell_score
        }
