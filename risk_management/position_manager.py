#!/usr/bin/env python3
"""
🚀 Professional Position Management System
ATR-based Stop Loss and Take Profit Calculation
Dynamic Risk Management and Position Sizing
Portfolio Risk Control and Correlation Analysis
"""
import numpy as np
import pandas as pd
import talib
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from enum import Enum

class PositionSide(Enum):
    LONG = "long"
    SHORT = "short"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"

@dataclass
class Position:
    symbol: str
    side: PositionSide
    entry_price: float
    quantity: float
    leverage: float
    stop_loss: float
    take_profit_levels: List[float]
    atr_at_entry: float
    timestamp: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    max_favorable_excursion: float = 0.0
    max_adverse_excursion: float = 0.0

@dataclass
class RiskLevels:
    symbol: str
    entry_price: float
    atr: float
    volatility_regime: str
    stop_loss_long: float
    stop_loss_short: float
    take_profit_long: List[float]
    take_profit_short: List[float]
    position_size_factor: float
    max_risk_percent: float
    risk_reward_ratios: List[float]
    timestamp: float

@dataclass
class PortfolioMetrics:
    total_value: float
    available_margin: float
    used_margin: float
    unrealized_pnl: float
    daily_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    total_trades: int
    risk_score: int  # 1-10 scale
    correlation_risk: float
    timestamp: float

class ATRPositionCalculator:
    """ATR-based Position Size and Risk Level Calculator"""
    
    def __init__(self, default_atr_period: int = 14):
        self.atr_period = default_atr_period
        self.risk_multipliers = {
            'conservative': {'sl': 1.5, 'tp': [2.0, 3.0, 4.0]},
            'moderate': {'sl': 2.0, 'tp': [2.5, 4.0, 6.0]},
            'aggressive': {'sl': 2.5, 'tp': [3.0, 5.0, 8.0]}
        }
        
    def calculate_atr_levels(self, 
                           high_prices: np.array, 
                           low_prices: np.array, 
                           close_prices: np.array,
                           risk_profile: str = 'moderate') -> RiskLevels:
        """Calculate ATR-based risk levels"""
        
        # Calculate ATR
        atr = talib.ATR(high_prices, low_prices, close_prices, timeperiod=self.atr_period)
        current_atr = atr[-1]
        current_price = close_prices[-1]
        
        # Get risk multipliers
        multipliers = self.risk_multipliers.get(risk_profile, self.risk_multipliers['moderate'])
        
        # Calculate stop loss levels
        stop_loss_long = current_price - (current_atr * multipliers['sl'])
        stop_loss_short = current_price + (current_atr * multipliers['sl'])
        
        # Calculate take profit levels
        take_profit_long = [current_price + (current_atr * mult) for mult in multipliers['tp']]
        take_profit_short = [current_price - (current_atr * mult) for mult in multipliers['tp']]
        
        # Calculate position size factor (inverse of volatility)
        position_size_factor = 1.0 / (current_atr / current_price)
        
        # Assess volatility regime
        atr_sma = np.mean(atr[-20:])  # 20-period average
        volatility_ratio = current_atr / atr_sma
        
        if volatility_ratio > 1.5:
            volatility_regime = 'high'
        elif volatility_ratio > 1.2:
            volatility_regime = 'elevated'
        elif volatility_ratio < 0.8:
            volatility_regime = 'low'
        else:
            volatility_regime = 'normal'
        
        # Calculate risk-reward ratios
        risk = current_atr * multipliers['sl']
        risk_reward_ratios = [(current_atr * mult) / risk for mult in multipliers['tp']]
        
        # Determine max risk percent based on volatility regime
        max_risk_mapping = {
            'low': 0.03,      # 3% risk per trade
            'normal': 0.02,   # 2% risk per trade
            'elevated': 0.015, # 1.5% risk per trade
            'high': 0.01      # 1% risk per trade
        }
        max_risk_percent = max_risk_mapping.get(volatility_regime, 0.02)
        
        return RiskLevels(
            symbol="",  # Will be set by caller
            entry_price=current_price,
            atr=current_atr,
            volatility_regime=volatility_regime,
            stop_loss_long=stop_loss_long,
            stop_loss_short=stop_loss_short,
            take_profit_long=take_profit_long,
            take_profit_short=take_profit_short,
            position_size_factor=position_size_factor,
            max_risk_percent=max_risk_percent,
            risk_reward_ratios=risk_reward_ratios,
            timestamp=datetime.now().timestamp()
        )
    
    def calculate_position_size(self, 
                              account_balance: float,
                              risk_levels: RiskLevels,
                              side: PositionSide,
                              leverage: float = 1.0,
                              max_risk_per_trade: float = 0.02) -> Dict:
        """Calculate optimal position size"""
        
        entry_price = risk_levels.entry_price
        stop_loss = risk_levels.stop_loss_long if side == PositionSide.LONG else risk_levels.stop_loss_short
        
        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss)
        risk_per_unit_percent = risk_per_unit / entry_price
        
        # Adjust risk based on volatility regime
        regime_multipliers = {
            'low': 1.2,
            'normal': 1.0,
            'elevated': 0.8,
            'high': 0.6
        }
        adjusted_risk = max_risk_per_trade * regime_multipliers.get(risk_levels.volatility_regime, 1.0)
        
        # Calculate position size
        risk_amount = account_balance * adjusted_risk
        base_position_size = risk_amount / risk_per_unit
        
        # Apply leverage
        leveraged_position_size = base_position_size * leverage
        
        # Calculate margin required
        position_value = leveraged_position_size * entry_price
        margin_required = position_value / leverage
        
        # Check if position fits within margin limits
        margin_ratio = margin_required / account_balance
        
        if margin_ratio > 0.8:  # Don't use more than 80% of account
            leveraged_position_size *= 0.8 / margin_ratio
            margin_required = account_balance * 0.8
        
        return {
            'position_size': leveraged_position_size,
            'position_value': leveraged_position_size * entry_price,
            'margin_required': margin_required,
            'risk_amount': risk_amount,
            'risk_percent': risk_amount / account_balance * 100,
            'potential_loss': risk_amount,
            'potential_profits': [leveraged_position_size * (tp - entry_price) if side == PositionSide.LONG 
                                 else leveraged_position_size * (entry_price - tp) 
                                 for tp in (risk_levels.take_profit_long if side == PositionSide.LONG 
                                           else risk_levels.take_profit_short)],
            'leverage_used': leverage,
            'margin_ratio': margin_ratio
        }

class DynamicStopLossManager:
    """Dynamic Stop Loss Management with Trailing and Breakeven"""
    
    def __init__(self):
        self.trailing_methods = ['atr', 'percentage', 'parabolic_sar']
        
    def calculate_trailing_stop(self, 
                              position: Position,
                              current_price: float,
                              high_prices: np.array,
                              low_prices: np.array,
                              close_prices: np.array,
                              method: str = 'atr') -> float:
        """Calculate trailing stop loss"""
        
        if method == 'atr':
            return self._atr_trailing_stop(position, current_price, high_prices, low_prices, close_prices)
        elif method == 'percentage':
            return self._percentage_trailing_stop(position, current_price)
        elif method == 'parabolic_sar':
            return self._parabolic_sar_stop(position, high_prices, low_prices, close_prices)
        else:
            return position.stop_loss
    
    def _atr_trailing_stop(self, position: Position, current_price: float,
                          high_prices: np.array, low_prices: np.array, close_prices: np.array) -> float:
        """ATR-based trailing stop"""
        current_atr = talib.ATR(high_prices, low_prices, close_prices, timeperiod=14)[-1]
        
        if position.side == PositionSide.LONG:
            # For long positions, trail stop up
            new_stop = current_price - (current_atr * 1.5)
            return max(position.stop_loss, new_stop)
        else:
            # For short positions, trail stop down
            new_stop = current_price + (current_atr * 1.5)
            return min(position.stop_loss, new_stop)
    
    def _percentage_trailing_stop(self, position: Position, current_price: float, trail_percent: float = 0.02) -> float:
        """Percentage-based trailing stop"""
        if position.side == PositionSide.LONG:
            new_stop = current_price * (1 - trail_percent)
            return max(position.stop_loss, new_stop)
        else:
            new_stop = current_price * (1 + trail_percent)
            return min(position.stop_loss, new_stop)
    
    def _parabolic_sar_stop(self, position: Position, high_prices: np.array, low_prices: np.array, close_prices: np.array) -> float:
        """Parabolic SAR trailing stop"""
        sar = talib.SAR(high_prices, low_prices)
        current_sar = sar[-1]
        
        if position.side == PositionSide.LONG:
            return max(position.stop_loss, current_sar)
        else:
            return min(position.stop_loss, current_sar)
    
    def should_move_to_breakeven(self, position: Position, current_price: float) -> bool:
        """Check if stop loss should be moved to breakeven"""
        if position.side == PositionSide.LONG:
            profit_distance = current_price - position.entry_price
            return profit_distance >= position.atr_at_entry * 1.0  # Move to BE after 1 ATR profit
        else:
            profit_distance = position.entry_price - current_price
            return profit_distance >= position.atr_at_entry * 1.0

class PortfolioRiskManager:
    """Portfolio-level Risk Management"""
    
    def __init__(self, max_portfolio_risk: float = 0.06, max_correlation: float = 0.7):
        self.max_portfolio_risk = max_portfolio_risk  # 6% max portfolio risk
        self.max_correlation = max_correlation
        self.position_calculator = ATRPositionCalculator()
        self.stop_manager = DynamicStopLossManager()
        
    def calculate_portfolio_risk(self, positions: List[Position], price_data: Dict[str, np.array]) -> float:
        """Calculate total portfolio risk"""
        total_risk = 0.0
        
        for position in positions:
            if position.symbol in price_data:
                current_price = price_data[position.symbol][-1]
                position_risk = abs(current_price - position.stop_loss) * position.quantity
                total_risk += position_risk
        
        return total_risk
    
    def calculate_correlation_matrix(self, price_data: Dict[str, np.array], window: int = 30) -> pd.DataFrame:
        """Calculate correlation matrix between symbols"""
        returns_data = {}
        
        for symbol, prices in price_data.items():
            if len(prices) > window:
                returns = np.diff(np.log(prices[-window:]))
                returns_data[symbol] = returns
        
        if not returns_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(returns_data)
        return df.corr()
    
    def check_correlation_risk(self, positions: List[Position], correlation_matrix: pd.DataFrame) -> Dict:
        """Check for excessive correlation risk"""
        symbols = [pos.symbol for pos in positions]
        correlation_risks = []
        
        for i, symbol1 in enumerate(symbols):
            for j, symbol2 in enumerate(symbols[i+1:], i+1):
                if symbol1 in correlation_matrix.index and symbol2 in correlation_matrix.columns:
                    corr = abs(correlation_matrix.loc[symbol1, symbol2])
                    if corr > self.max_correlation:
                        correlation_risks.append({
                            'pair': (symbol1, symbol2),
                            'correlation': corr,
                            'risk_level': 'high' if corr > 0.8 else 'medium'
                        })
        
        return {
            'high_correlations': correlation_risks,
            'max_correlation': max([risk['correlation'] for risk in correlation_risks]) if correlation_risks else 0,
            'correlation_risk_score': len(correlation_risks)
        }
    
    def update_positions(self, positions: List[Position], 
                        current_prices: Dict[str, float],
                        price_history: Dict[str, Dict[str, np.array]]) -> List[Position]:
        """Update all positions with current prices and dynamic stops"""
        updated_positions = []
        
        for position in positions:
            if position.symbol in current_prices:
                current_price = current_prices[position.symbol]
                
                # Update P&L
                if position.side == PositionSide.LONG:
                    position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
                else:
                    position.unrealized_pnl = (position.entry_price - current_price) * position.quantity
                
                # Update max favorable/adverse excursion
                if position.unrealized_pnl > position.max_favorable_excursion:
                    position.max_favorable_excursion = position.unrealized_pnl
                
                if position.unrealized_pnl < 0 and abs(position.unrealized_pnl) > position.max_adverse_excursion:
                    position.max_adverse_excursion = abs(position.unrealized_pnl)
                
                # Update dynamic stop loss
                if position.symbol in price_history:
                    symbol_data = price_history[position.symbol]
                    new_stop = self.stop_manager.calculate_trailing_stop(
                        position, current_price,
                        symbol_data['high'], symbol_data['low'], symbol_data['close']
                    )
                    position.stop_loss = new_stop
                
                # Move to breakeven if profitable enough
                if self.stop_manager.should_move_to_breakeven(position, current_price):
                    position.stop_loss = position.entry_price
                
                updated_positions.append(position)
        
        return updated_positions
    
    def generate_portfolio_metrics(self, 
                                 positions: List[Position],
                                 account_balance: float,
                                 trade_history: List[Dict] = None) -> PortfolioMetrics:
        """Generate comprehensive portfolio metrics"""
        
        # Calculate basic metrics
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)
        used_margin = sum(pos.quantity * pos.entry_price / pos.leverage for pos in positions)
        available_margin = account_balance - used_margin
        
        # Calculate performance metrics from trade history
        if trade_history:
            profits = [trade['pnl'] for trade in trade_history if trade['pnl'] > 0]
            losses = [trade['pnl'] for trade in trade_history if trade['pnl'] < 0]
            
            win_rate = len(profits) / len(trade_history) if trade_history else 0
            avg_win = np.mean(profits) if profits else 0
            avg_loss = np.mean(losses) if losses else 0
            profit_factor = abs(sum(profits) / sum(losses)) if losses else float('inf')
            
            # Calculate Sharpe ratio (simplified)
            daily_returns = [trade['pnl'] / account_balance for trade in trade_history]
            sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) if len(daily_returns) > 1 else 0
            
            # Calculate max drawdown
            cumulative_pnl = np.cumsum([trade['pnl'] for trade in trade_history])
            peak = np.maximum.accumulate(cumulative_pnl)
            drawdown = (cumulative_pnl - peak) / peak
            max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
        else:
            win_rate = avg_win = avg_loss = profit_factor = sharpe_ratio = max_drawdown = 0
        
        # Calculate risk score (1-10)
        margin_usage = used_margin / account_balance if account_balance > 0 else 0
        portfolio_risk = sum(abs(pos.unrealized_pnl) for pos in positions if pos.unrealized_pnl < 0)
        risk_ratio = portfolio_risk / account_balance if account_balance > 0 else 0
        
        risk_score = int(min(10, max(1, (margin_usage * 5) + (risk_ratio * 5))))
        
        return PortfolioMetrics(
            total_value=account_balance + total_unrealized_pnl,
            available_margin=available_margin,
            used_margin=used_margin,
            unrealized_pnl=total_unrealized_pnl,
            daily_pnl=sum(trade['pnl'] for trade in trade_history[-1:]) if trade_history else 0,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            total_trades=len(trade_history) if trade_history else 0,
            risk_score=risk_score,
            correlation_risk=0.0,  # Will be calculated separately
            timestamp=datetime.now().timestamp()
        )

class SignalValidator:
    """Validate trading signals against risk management rules"""
    
    def __init__(self, portfolio_manager: PortfolioRiskManager):
        self.portfolio_manager = portfolio_manager
        
    def validate_signal(self, 
                       signal: Dict,
                       current_positions: List[Position],
                       account_balance: float,
                       price_history: Dict[str, Dict[str, np.array]]) -> Dict:
        """Validate if a signal should be executed"""
        
        symbol = signal['symbol']
        side = PositionSide.LONG if signal['action'] in ['BUY', 'STRONG_BUY'] else PositionSide.SHORT
        
        # Check if symbol data is available
        if symbol not in price_history:
            return {'valid': False, 'reason': 'No price history available'}
        
        # Calculate risk levels
        symbol_data = price_history[symbol]
        risk_levels = self.portfolio_manager.position_calculator.calculate_atr_levels(
            symbol_data['high'], symbol_data['low'], symbol_data['close']
        )
        risk_levels.symbol = symbol
        
        # Calculate position size
        leverage = min(signal.get('leverage_recommendation', 1), 10)  # Cap at 10x
        position_calc = self.portfolio_manager.position_calculator.calculate_position_size(
            account_balance, risk_levels, side, leverage
        )
        
        # Check portfolio risk limits
        current_portfolio_risk = self.portfolio_manager.calculate_portfolio_risk(
            current_positions, {pos.symbol: np.array([risk_levels.entry_price]) for pos in current_positions}
        )
        
        additional_risk = position_calc['risk_amount']
        total_risk_ratio = (current_portfolio_risk + additional_risk) / account_balance
        
        if total_risk_ratio > self.portfolio_manager.max_portfolio_risk:
            return {
                'valid': False, 
                'reason': f'Portfolio risk limit exceeded: {total_risk_ratio:.1%} > {self.portfolio_manager.max_portfolio_risk:.1%}'
            }
        
        # Check margin requirements
        if position_calc['margin_ratio'] > 0.8:
            return {
                'valid': False,
                'reason': f'Insufficient margin: requires {position_calc["margin_ratio"]:.1%} of account'
            }
        
        # Check correlation risk
        position_symbols = [pos.symbol for pos in current_positions]
        if symbol in position_symbols:
            return {
                'valid': False,
                'reason': 'Position already exists for this symbol'
            }
        
        return {
            'valid': True,
            'risk_levels': risk_levels,
            'position_calc': position_calc,
            'recommended_action': {
                'symbol': symbol,
                'side': side.value,
                'entry_price': risk_levels.entry_price,
                'quantity': position_calc['position_size'],
                'leverage': leverage,
                'stop_loss': risk_levels.stop_loss_long if side == PositionSide.LONG else risk_levels.stop_loss_short,
                'take_profit_levels': risk_levels.take_profit_long if side == PositionSide.LONG else risk_levels.take_profit_short,
                'risk_amount': position_calc['risk_amount'],
                'risk_reward_ratios': risk_levels.risk_reward_ratios
            }
        }

# Example usage
if __name__ == "__main__":
    print("🚀 Testing Position Management System...")
    
    # Generate sample data
    np.random.seed(42)
    n_points = 200
    
    # Sample OHLC data
    closes = 100 + np.cumsum(np.random.normal(0, 1, n_points))
    highs = closes + np.random.uniform(0.5, 2.0, n_points)
    lows = closes - np.random.uniform(0.5, 2.0, n_points)
    
    # Test ATR Position Calculator
    calculator = ATRPositionCalculator()
    risk_levels = calculator.calculate_atr_levels(highs, lows, closes)
    
    print(f"✅ ATR Risk Levels calculated:")
    print(f"Entry Price: ${risk_levels.entry_price:.2f}")
    print(f"Stop Loss (Long): ${risk_levels.stop_loss_long:.2f}")
    print(f"Take Profit Levels: {[f'${tp:.2f}' for tp in risk_levels.take_profit_long]}")
    print(f"Volatility Regime: {risk_levels.volatility_regime}")
    print(f"Risk/Reward Ratios: {[f'{rr:.1f}:1' for rr in risk_levels.risk_reward_ratios]}")
    
    # Test Position Size Calculation
    account_balance = 10000
    position_calc = calculator.calculate_position_size(
        account_balance, risk_levels, PositionSide.LONG, leverage=3.0
    )
    
    print(f"\n✅ Position Size calculated:")
    print(f"Position Size: {position_calc['position_size']:.4f}")
    print(f"Risk Amount: ${position_calc['risk_amount']:.2f}")
    print(f"Risk Percent: {position_calc['risk_percent']:.2f}%")
    print(f"Margin Required: ${position_calc['margin_required']:.2f}")
    print(f"Potential Profits: {[f'${profit:.2f}' for profit in position_calc['potential_profits']]}")
    
    print("\n🎯 Position Management System ready!") 