# src/strategies/signal_generator.py
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import pandas as pd
import numpy as np

# Imports
from src.core.settings import settings
from src.strategies.models import EnhancedSignal, MarketRegime
from src.strategies.market_regime import EnhancedMarketRegimeAnalyzer
from src.strategies.adaptive_indicators import ImprovedAdaptiveIndicatorEngine
from src.strategies.feature_engine import SmartFeatureEngineer
from src.strategies.pattern_validator import PatternValidator
from src.strategies.risk_manager import DynamicRiskManager
from src.strategies.ml_engine import CalibratedMLEngine

logger = logging.getLogger(__name__)

class SignalGenerator:
    def __init__(self, exchange_connector):
        self.exchange = exchange_connector
        self.config = settings
        
        self.regime_analyzer = EnhancedMarketRegimeAnalyzer(exchange_connector)
        self.indicator_engine = ImprovedAdaptiveIndicatorEngine()
        self.feature_engineer = SmartFeatureEngineer()
        self.risk_manager = DynamicRiskManager()
        self.ml_engine = CalibratedMLEngine()
        self.pattern_validator = PatternValidator({}) # Load history on start
        
        self.signal_cache = {}

    async def analyze_symbol(self, symbol: str, multi_tf_data: Dict[str, pd.DataFrame]) -> Optional[EnhancedSignal]:
        if symbol in self.signal_cache:
            last_sig, last_time = self.signal_cache[symbol]
            if (datetime.now() - last_time).total_seconds() < self.config.signal_cooldown_minutes * 60:
                return None

        try:
            primary_tf = self.config.primary_timeframe
            primary_data = multi_tf_data.get(primary_tf)
            
            if primary_data is None or len(primary_data) < 100: return None

            # 1. Regime
            regime = await self.regime_analyzer.detect_regime(primary_data, symbol)
            if regime.crisis_mode and not getattr(self.config, 'trade_in_crisis', False): return None

            # 2. Indicators
            indicators = self.indicator_engine.calculate_adaptive_indicators(primary_data, regime)
            rsi, oversold, overbought = self.indicator_engine.calculate_adaptive_rsi(primary_data, regime)
            indicators['rsi'] = rsi

            # 3. TA Signal
            ta_signal = self._generate_ta_signal(primary_data, indicators, oversold, overbought)
            if ta_signal['confidence'] < 0.3: return None

            # 4. Features
            features = self.feature_engineer.create_features(primary_data, regime, indicators)

            # 5. ML
            ml_prob = await self.ml_engine.predict_probability(features)

            # 6. Validation
            validation = self.pattern_validator.validate_signal(symbol, features, primary_data['close'].iloc[-1])

            # 7. Combine
            combined = self._combine_signals(ta_signal, ml_prob, validation, regime, features)
            if combined['confidence'] < self.config.min_confidence: return None

            # 8. Risk Management (FULL CALCULATION)
            final_signal = await self._apply_risk_management(symbol, combined, primary_data, regime, indicators)
            
            self.signal_cache[symbol] = (final_signal, datetime.now())
            return final_signal
        except Exception as e:
            logger.exception(f"Signal Gen Error {symbol}: {e}")
            return None

    def _generate_ta_signal(self, data: pd.DataFrame, indicators: Dict, oversold: int, overbought: int) -> Dict:
        current_price = data['close'].iloc[-1]
        current_rsi = indicators['rsi'].iloc[-1]
        buy_score, sell_score = 0, 0
        confidence = 0.0
        
        if current_rsi < oversold: buy_score += 2; confidence += 0.2
        elif current_rsi > overbought: sell_score += 2; confidence += 0.2
        
        if indicators['ema_cross'].iloc[-1]: buy_score += 1
        else: sell_score += 1
        confidence += 0.15
        
        if indicators['macd_hist'].iloc[-1] > 0: buy_score += 1
        else: sell_score += 1
        
        direction = 'BUY' if buy_score >= 3 and buy_score > sell_score else 'SELL' if sell_score >= 3 else 'NEUTRAL'
        if direction == 'NEUTRAL': confidence = 0.3
        else: confidence = min(0.9, confidence + abs(buy_score - sell_score)*0.05)
        
        return {'direction': direction, 'confidence': confidence, 'buy_score': buy_score, 'sell_score': sell_score}

    def _combine_signals(self, ta, ml, val, reg, feat) -> Dict:
        base_conf = ta['confidence']
        if ml > 0.7: base_conf *= 1.2
        elif ml < 0.3: base_conf *= 0.8
        
        base_conf += val.get('confidence_boost', 0)
        if feat.get('volume_ratio', 1) > 1.8: base_conf *= 1.05
        
        if (reg.trend == 'bullish' and ta['direction'] == 'BUY') or (reg.trend == 'bearish' and ta['direction'] == 'SELL'):
            base_conf *= 1.1
        if reg.crisis_mode: base_conf *= 0.7
            
        return {
            'direction': ta['direction'],
            'confidence': min(0.95, base_conf),
            'ta_confidence': ta['confidence'],
            'ml_probability': ml,
            'validation_score': val.get('similarity_score', 0.5)
        }

    async def _apply_risk_management(self, symbol: str, signal: Dict, data: pd.DataFrame, 
                                     regime: MarketRegime, indicators: Dict) -> EnhancedSignal:
        """FULL RISK MANAGEMENT LOGIC FROM ORIGINAL"""
        
        current_price = data['close'].iloc[-1]
        volatility = regime.volatility_value / 100
        atr = indicators['atr'].iloc[-1]
        
        # 1. Calculate Stop Loss & TP
        risk_params = self.risk_manager.calculate_dynamic_levels(
            entry_price=current_price,
            atr=atr,
            volatility=volatility,
            trend_direction="long" if signal['direction'] == 'BUY' else "short",
            regime_strength=regime.strength
        )
        
        stop_loss = risk_params['stop_loss']
        take_profits = risk_params['take_profit']
        
        # 2. Calculate Position Size
        pos_info = self.risk_manager.calculate_position_size(
            symbol, current_price, stop_loss, signal['confidence'], volatility, atr
        )
        
        # 3. Calculate Risk Metrics
        risk_distance = abs(current_price - stop_loss)
        
        # Average TP
        avg_tp = np.mean([abs(tp - current_price) for tp in take_profits])
        
        # Risk/Reward Ratio
        risk_reward = avg_tp / risk_distance if risk_distance > 0 else 1.0
        
        # Historical Win Rate Estimation
        historical_win_rate = 0.5 + (signal['confidence'] - 0.5) * 0.5
        
        # Expected Value Calculation
        expected_value = (historical_win_rate * avg_tp - (1 - historical_win_rate) * risk_distance)
        
        # VAR 95 & Max Drawdown Risk
        var_95 = risk_distance * 1.645 / current_price * 100
        max_drawdown_risk = risk_distance * 2 / current_price * 100
        
        # 4. Build Signal Object
        return EnhancedSignal(
            symbol=symbol,
            direction='STRONG_BUY' if signal['confidence'] > 0.8 and signal['direction'] == 'BUY' else 
                     'STRONG_SELL' if signal['confidence'] > 0.8 and signal['direction'] == 'SELL' else 
                     signal['direction'],
            confidence=signal['confidence'],
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=tuple(take_profits),
            position_size_pct=pos_info['position_size_pct'],
            expected_value=expected_value / current_price * 100, 
            risk_reward=risk_reward,
            timeframe=self.config.primary_timeframe,
            rationale={
                'ta_score': signal['ta_confidence'],
                'ml_probability': signal['ml_probability'],
                'validation_score': signal['validation_score'],
                'regime': regime.trend,
                'volatility': regime.volatility
            },
            valid_until=datetime.now() + timedelta(hours=2),
            model_agreement={
                'ta': signal['ta_confidence'],
                'ml': signal['ml_probability'],
                'validation': signal['validation_score']
            },
            var_95=var_95,
            max_drawdown_risk=max_drawdown_risk,
            kelly_fraction=pos_info['kelly_fraction']
        )
