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
from src.strategies.onchain_analyzer import OnChainAnalyzer
from src.strategies.ai_engine import AdvancedNeuralCore

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
        self.ai_neural_core = AdvancedNeuralCore()
        self.onchain_analyzer = OnChainAnalyzer()
        self.pattern_validator = PatternValidator({}) # Load history on start
        
        self.signal_cache = {}

    async def analyze_symbol(self, symbol: str, multi_tf_data: Dict[str, pd.DataFrame], target_timeframe: str = None) -> Optional[EnhancedSignal]:
        """Analyze symbol for a specific timeframe. If no target_timeframe specified, use primary_timeframe."""
        
        # Use target timeframe or fall back to primary
        timeframe = target_timeframe or self.config.primary_timeframe
        cache_key = f"{symbol}_{timeframe}"
        
        if cache_key in self.signal_cache:
            last_sig, last_time = self.signal_cache[cache_key]
            if (datetime.now() - last_time).total_seconds() < self.config.signal_cooldown_minutes * 60:
                return None

        try:
            primary_data = multi_tf_data.get(timeframe)
            
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

            # 7. On-Chain Metrics (New)
            onchain_data = await self.onchain_analyzer.get_metrics(symbol)

            # 8. Neural AI Synthesis (Gemini Upgrade)
            ai_synthesis = await self.ai_neural_core.process_signal(
                symbol, primary_data, regime, indicators, onchain_data, features
            )

            # 9. Combine
            combined = self._combine_signals(ta_signal, ml_prob, validation, regime, features, ai_synthesis)
            
            # Diagnostic: Log near-miss signals
            if combined['confidence'] < self.config.min_confidence:
                logger.info(
                    f"[NEAR-MISS] {symbol} ({timeframe}): Confidence {combined['confidence']:.2f} < Threshold {self.config.min_confidence} | "
                    f"Direction: {combined['direction']}, TA: {ta_signal['confidence']:.2f}, "
                    f"BuyScore: {ta_signal.get('buy_score', 0):.1f}, SellScore: {ta_signal.get('sell_score', 0):.1f}"
                )
                return None

            # 10. Risk Management (FULL CALCULATION)
            final_signal = await self._apply_risk_management(
                symbol, combined, primary_data, regime, indicators, onchain_data, ai_synthesis, timeframe
            )
            
            self.signal_cache[cache_key] = (final_signal, datetime.now())
            return final_signal
        except Exception as e:
            logger.exception(f"Signal Gen Error {symbol} ({timeframe}): {e}")
            return None

    def _generate_ta_signal(self, data: pd.DataFrame, indicators: Dict, oversold: int, overbought: int) -> Dict:
        current_price = data['close'].iloc[-1]
        current_rsi = indicators['rsi'].iloc[-1]
        buy_score, sell_score = 0, 0
        confidence = 0.0
        
        # 1. RSI Signal (weighted lower to allow trend-following)
        if current_rsi < oversold: 
            buy_score += 1.5
            confidence += 0.15
        elif current_rsi > overbought: 
            sell_score += 1.5
            confidence += 0.15
        
        # 2. EMA Cross (critical trend indicator)
        if indicators['ema_cross'].iloc[-1]: 
            buy_score += 2
            confidence += 0.2
        else: 
            sell_score += 2
            confidence += 0.2
        
        # 3. MACD Histogram
        macd_hist = indicators['macd_hist'].iloc[-1]
        if macd_hist > 0: 
            buy_score += 1
            confidence += 0.1
        elif macd_hist < 0:
            sell_score += 1
            confidence += 0.1
        
        # 4. ADX (trend strength) - NEW
        adx = indicators.get('adx', pd.Series([0])).iloc[-1]
        if adx > 25:  # Strong trend
            confidence += 0.15
            # Add to the dominant direction
            if buy_score > sell_score:
                buy_score += 1
            else:
                sell_score += 1
        
        # 5. Bollinger Bands (volatility breakout) - NEW
        bb_upper = indicators['bb_upper'].iloc[-1]
        bb_lower = indicators['bb_lower'].iloc[-1]
        if current_price <= bb_lower:
            buy_score += 1.5
            confidence += 0.12
        elif current_price >= bb_upper:
            sell_score += 1.5
            confidence += 0.12
        
        # Direction determination (lowered threshold from 3 to 2.5)
        total_buy = buy_score
        total_sell = sell_score
        
        if total_buy >= 2.5 and total_buy > total_sell:
            direction = 'BUY'
        elif total_sell >= 2.5 and total_sell > total_buy:
            direction = 'SELL'
        else:
            direction = 'NEUTRAL'
            confidence = 0.35  # Slightly higher neutral confidence
        
        if direction != 'NEUTRAL':
            # Boost confidence based on score difference
            confidence = min(0.92, confidence + abs(total_buy - total_sell) * 0.06)
        
        return {
            'direction': direction, 
            'confidence': confidence, 
            'buy_score': total_buy, 
            'sell_score': total_sell
        }

    def _combine_signals(self, ta, ml, val, reg, feat, ai=None) -> Dict:
        base_conf = ta['confidence']
        
        # ML heuristic weighting
        if ml > 0.7: base_conf *= 1.2
        elif ml < 0.3: base_conf *= 0.8
        
        # AI Neural Synthesis Weighting (Gemini) - OPTIONAL
        if ai and isinstance(ai, dict) and 'confidence' in ai:
            # Weighted consensus: 60% TA/ML + 40% AI/On-Chain (when available)
            ai_conf = ai['confidence']  # 0.0 to 1.0 from Gemini
            base_conf = (base_conf * 0.60) + (ai_conf * 0.40)
        # If AI is unavailable, rely fully on TA/ML

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
                                     regime: MarketRegime, indicators: Dict, 
                                     onchain=None, ai=None, timeframe: str = '1h') -> EnhancedSignal:
        """FULL RISK MANAGEMENT LOGIC FROM ORIGINAL"""
        
        current_price = data['close'].iloc[-1]
        volatility = regime.volatility_value / 100
        atr = indicators['atr'].iloc[-1]
        adx = indicators['adx'].iloc[-1] if 'adx' in indicators else 20.0
        
        # 1. Calculate Stop Loss & TP (Passing ADX and Phase)
        risk_params = self.risk_manager.calculate_dynamic_levels(
            entry_price=current_price,
            atr=atr,
            volatility=regime.volatility, # Pass string state ('low', 'medium', 'high')
            trend_direction="long" if signal['direction'] in ['BUY', 'STRONG_BUY'] else "short",
            adx=adx,
            phase=regime.phase,
            crisis_mode=regime.crisis_mode
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
            timeframe=timeframe,  # Use the actual analyzed timeframe
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
