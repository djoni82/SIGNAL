# src/strategies/risk_manager.py
from collections import deque
import numpy as np
from src.core.settings import settings
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

class DynamicRiskManager:
    def __init__(self):
        self.trade_history = deque(maxlen=100)
        # Initial stats for calculation
        self.win_loss_stats = {'avg_win': 0.02, 'avg_loss': -0.01, 'count': 0}
        
    def record_trade(self, symbol: str, profit_pct: float):
        """Record trade for statistics"""
        self.trade_history.append({
            'symbol': symbol,
            'timestamp': None, # Can add datetime.now()
            'profit_pct': profit_pct
        })
        
        if profit_pct > 0:
            # Weighted average update
            old_avg = self.win_loss_stats['avg_win']
            count = self.win_loss_stats['count']
            self.win_loss_stats['avg_win'] = (old_avg * count + profit_pct) / (count + 1)
        else:
            old_avg = self.win_loss_stats['avg_loss']
            count = self.win_loss_stats['count']
            self.win_loss_stats['avg_loss'] = (old_avg * count + profit_pct) / (count + 1)
            
        self.win_loss_stats['count'] += 1

    def _calculate_dynamic_win_loss_ratio(self) -> float:
        """Calculates dynamic R:R based on history"""
        if self.win_loss_stats['count'] < 10:
            return 2.0  # Default
        
        recent_trades = list(self.trade_history)[-20:]
        if not recent_trades: return 2.0
        
        wins = [t['profit_pct'] for t in recent_trades if t['profit_pct'] > 0]
        losses = [t['profit_pct'] for t in recent_trades if t['profit_pct'] < 0]
        
        if not wins or not losses: return 2.0
        
        avg_win = np.mean(wins)
        avg_loss = abs(np.mean(losses))
        
        ratio = avg_win / avg_loss if avg_loss > 0 else 3.0
        return min(5.0, max(1.0, ratio))

    def calculate_position_size(self, symbol: str, entry_price: float, 
                                stop_loss: float, confidence: float, 
                                volatility: float, atr: float) -> Dict:
        """Calculates position size with dynamic R:R"""
        stop_distance_pct = abs(entry_price - stop_loss) / entry_price
        win_loss_ratio = self._calculate_dynamic_win_loss_ratio()
        
        # Kelly Criterion
        win_rate = 0.5 + (confidence - 0.5) * 0.5
        kelly_fraction = win_rate - ((1 - win_rate) / win_loss_ratio)
        kelly_fraction = max(0.01, min(kelly_fraction, 0.25))
        
        # Volatility adjustment
        volatility_multiplier = 0.7 if volatility > 0.03 else (0.9 if volatility > 0.015 else 1.0)
        if volatility > 0.05: volatility_multiplier *= 0.5 # Crisis mode
        
        position_value = settings.initial_capital * kelly_fraction * volatility_multiplier
        
        # Risk limits
        max_risk_amount = settings.initial_capital * settings.max_position_size_pct
        risk_amount = position_value * stop_distance_pct
        
        if risk_amount > max_risk_amount:
            position_value = max_risk_amount / stop_distance_pct
            
        units = position_value / entry_price
        
        return {
            'position_value': position_value,
            'units': units,
            'risk_amount': risk_amount,
            'risk_percentage': stop_distance_pct * 100,
            'kelly_fraction': kelly_fraction,
            'position_size_pct': (position_value / settings.initial_capital) * 100,
            'win_loss_ratio': win_loss_ratio
        }

    def calculate_dynamic_levels(self, entry_price: float, atr: float, volatility: float, 
                                 trend_direction: str, adx: float = 20.0, 
                                 phase: str = 'markup', crisis_mode: bool = False, **kwargs) -> Dict:
        """
        Advanced dynamic level calculation ported from SignalPro Alpha.
        Uses ADX for trend tightening and Market Phase for buffers.
        """
        # 1. STOP-LOSS (SL) CALCULATION
        # Base multiplier based on volatility state
        if volatility == 'high':
            base_multiplier = 3.2
        elif volatility == 'medium':
            base_multiplier = 2.4
        else: # low
            base_multiplier = 1.8
            
        if crisis_mode:
            base_multiplier = 4.5

        # Trend tightening based on ADX (stronger trend = tighter stops)
        trend_tightening = 0.85 if adx > 30 else (0.95 if adx > 20 else 1.15)
        
        # Phase buffer (wider stops during accumulation/distribution)
        phase_buffer = 1.2 if phase in ['accumulation', 'distribution'] else 1.0
        if crisis_mode:
            phase_buffer *= 1.4

        final_sl_multiplier = base_multiplier * trend_tightening * phase_buffer
        stop_dist = atr * final_sl_multiplier
        
        # Minimum stop loss (0.5%)
        min_stop = entry_price * 0.005
        stop_distance = max(min_stop, stop_dist)
        
        is_long = trend_direction == 'long'
        sl_price = entry_price - stop_distance if is_long else entry_price + stop_distance

        # 2. TAKE-PROFIT (TP) CALCULATION
        # TP Expansion based on ADX
        tp_expansion = 1.6 if adx > 35 else (1.2 if adx > 20 else 0.9)
        if phase in ['markup', 'markdown']:
            tp_expansion *= 1.25
        
        # Original 3-level TP logic but with expansion
        tp1_dist = stop_distance * 1.5 * tp_expansion
        tp2_dist = stop_distance * 3.0 * tp_expansion
        tp3_dist = stop_distance * 6.0 * tp_expansion

        if is_long:
            tp1 = entry_price + tp1_dist
            tp2 = entry_price + tp2_dist
            tp3 = entry_price + tp3_dist
        else:
            tp1 = entry_price - tp1_dist
            tp2 = entry_price - tp2_dist
            tp3 = entry_price - tp3_dist
            
        take_profits = (tp1, tp2, tp3)
        
        # Trailing stop distance
        trailing_stop_dist = atr * 1.6 * (2.5 if crisis_mode else 1.0)
            
        return {
            'stop_loss': sl_price,
            'take_profit': take_profits,
            'stop_loss_distance': stop_distance,
            'trailing_stop_distance': trailing_stop_dist,
            'risk_reward': (abs(tp2 - entry_price) / stop_distance)
        }
