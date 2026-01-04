import pandas as pd
import numpy as np
from src.strategies.models import MarketRegime

class EnhancedMarketRegimeAnalyzer:
    def __init__(self, exchange_connector):
        self.exchange = exchange_connector

    async def detect_regime(self, data: pd.DataFrame, symbol: str) -> MarketRegime:
        # Fallback implementation reusing logic from original unified_signal_bot.py
        
        # Calculate Volatility
        data['returns'] = data['close'].pct_change()
        volatility_val = data['returns'].std() * np.sqrt(252) # Annualized
        
        if volatility_val < 0.3: volatility_state = 'low'
        elif volatility_val < 0.6: volatility_state = 'medium'
        else: volatility_state = 'high'
        
        # Crisis Mode Detection (e.g. > 5% drop in last few candles or extreme volatility)
        recent_drop = (data['close'].iloc[-1] - data['close'].iloc[-5]) / data['close'].iloc[-5]
        crisis_mode = volatility_val > 0.8 or recent_drop < -0.10

        # Trend and Phase (Simplified Wyckoff/Trend logic)
        sma50 = data['close'].rolling(50).mean().iloc[-1]
        sma200 = data['close'].rolling(200).mean().iloc[-1]
        current_price = data['close'].iloc[-1]
        
        if current_price > sma50 and sma50 > sma200:
            trend = 'bullish'
            phase = 'markup'
        elif current_price < sma50 and sma50 < sma200:
            trend = 'bearish'
            phase = 'markdown'
        else:
            trend = 'neutral'
            phase = 'accumulation' if current_price < sma50 else 'distribution'
            
        strength = abs(current_price - sma50) / sma50 * 100 # Simple strength proxy

        return MarketRegime(
            trend=trend,
            phase=phase,
            strength=strength,
            volatility=volatility_state,
            volatility_value=volatility_val,
            crisis_mode=crisis_mode
        )
