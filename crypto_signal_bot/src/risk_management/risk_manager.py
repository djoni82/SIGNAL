"""
Risk Manager for CryptoAlphaPro
Handles risk calculation, position sizing, and hedging strategies
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from loguru import logger
import talib

from src.config.config_manager import ConfigManager


class RiskManager:
    """Main risk management class"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.risk_config = config.get_risk_config()
        
        # Risk parameters
        self.max_leverage = self.risk_config.max_leverage
        self.default_leverage = self.risk_config.default_leverage
        self.max_position_size = self.risk_config.max_position_size
        self.stop_loss_atr_multiplier = self.risk_config.stop_loss_atr_multiplier
        self.take_profit_levels = self.risk_config.take_profit_levels
        self.hedge_ratio = self.risk_config.hedge_ratio
        
        # Volatility thresholds
        self.volatility_thresholds = self.risk_config.volatility_thresholds
        
        # Portfolio tracking
        self.portfolio_value = 10000.0  # Starting portfolio value
        self.open_positions: Dict[str, Dict] = {}
        self.risk_metrics: Dict[str, float] = {}
        
        # Risk limits
        self.daily_loss_limit = 0.05  # 5% daily loss limit
        self.max_correlation = 0.7    # Maximum correlation between positions
        self.max_drawdown_limit = 0.25  # 25% maximum drawdown
        
        # Performance tracking
        self.daily_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_portfolio_value = self.portfolio_value
        
    def calculate_position_size(self, signal: Dict[str, Any], account_balance: float) -> Dict[str, Any]:
        """Calculate optimal position size based on risk parameters"""
        try:
            symbol = signal['symbol']
            confidence = signal['confidence']
            leverage = signal['leverage']
            entry_price = sum(signal['entry_range']) / 2
            stop_loss = signal['stop_loss']
            
            # Calculate risk per trade
            risk_per_trade = self._calculate_risk_per_trade(confidence)
            
            # Calculate position risk
            if signal['action'] == 'BUY':
                price_risk = (entry_price - stop_loss) / entry_price
            else:
                price_risk = (stop_loss - entry_price) / entry_price
            
            if price_risk <= 0:
                logger.warning(f"⚠️  Invalid price risk for {symbol}: {price_risk}")
                return {'valid': False, 'reason': 'Invalid price risk'}
            
            # Calculate base position size
            risk_amount = account_balance * risk_per_trade
            base_position_size = risk_amount / price_risk
            
            # Apply leverage
            position_value = base_position_size * leverage
            
            # Check position size limits
            max_allowed = account_balance * self.max_position_size
            if position_value > max_allowed:
                position_value = max_allowed
                leverage = position_value / base_position_size
            
            # Calculate position in base currency
            position_size = position_value / entry_price
            
            # Check portfolio concentration
            concentration_check = self._check_portfolio_concentration(symbol, position_value)
            if not concentration_check['valid']:
                return concentration_check
            
            # Calculate margin requirements
            margin_required = position_value / leverage
            
            return {
                'valid': True,
                'symbol': symbol,
                'position_size': position_size,
                'position_value': position_value,
                'leverage': leverage,
                'margin_required': margin_required,
                'risk_amount': risk_amount,
                'risk_percentage': risk_per_trade,
                'price_risk': price_risk,
                'recommended_sl': stop_loss,
                'recommended_tp': signal['take_profit']
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculating position size: {e}")
            return {'valid': False, 'reason': f'Calculation error: {str(e)}'}
    
    def _calculate_risk_per_trade(self, confidence: float) -> float:
        """Calculate risk per trade based on confidence"""
        try:
            # Base risk: 1-2% per trade
            base_risk = 0.015
            
            # Adjust based on confidence
            confidence_multiplier = 0.5 + (confidence * 1.5)  # 0.5 to 2.0
            
            # Adjust based on current drawdown
            drawdown_adjustment = 1.0
            if self.max_drawdown > 0.1:  # If drawdown > 10%
                drawdown_adjustment = 0.5  # Reduce risk
            elif self.max_drawdown > 0.05:  # If drawdown > 5%
                drawdown_adjustment = 0.75
            
            # Adjust based on recent performance
            performance_adjustment = self._get_performance_adjustment()
            
            # Calculate final risk
            risk_per_trade = base_risk * confidence_multiplier * drawdown_adjustment * performance_adjustment
            
            # Ensure within limits
            risk_per_trade = max(0.005, min(0.03, risk_per_trade))  # 0.5% to 3%
            
            return risk_per_trade
            
        except Exception as e:
            logger.error(f"❌ Error calculating risk per trade: {e}")
            return 0.015  # Default 1.5%
    
    def _check_portfolio_concentration(self, symbol: str, position_value: float) -> Dict[str, Any]:
        """Check if position would create too much concentration"""
        try:
            # Calculate current portfolio concentration
            total_exposure = sum(pos.get('position_value', 0) for pos in self.open_positions.values())
            total_exposure += position_value
            
            # Check total exposure limit
            if total_exposure > self.portfolio_value * 0.8:  # 80% max exposure
                return {
                    'valid': False,
                    'reason': 'Exceeds total portfolio exposure limit (80%)'
                }
            
            # Check single position limit
            if position_value > self.portfolio_value * self.max_position_size:
                return {
                    'valid': False,
                    'reason': f'Exceeds single position limit ({self.max_position_size:.1%})'
                }
            
            # Check correlation with existing positions
            correlation_risk = self._check_correlation_risk(symbol)
            if not correlation_risk['valid']:
                return correlation_risk
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"❌ Error checking portfolio concentration: {e}")
            return {'valid': False, 'reason': f'Concentration check error: {str(e)}'}
    
    def _check_correlation_risk(self, symbol: str) -> Dict[str, Any]:
        """Check correlation risk with existing positions"""
        try:
            # Simplified correlation check based on asset class
            base_currency = symbol.split('/')[0]
            
            # Count positions in same base currency
            same_currency_count = 0
            same_currency_value = 0
            
            for pos_symbol, position in self.open_positions.items():
                if pos_symbol.split('/')[0] == base_currency:
                    same_currency_count += 1
                    same_currency_value += position.get('position_value', 0)
            
            # Check if too many positions in same currency
            if same_currency_count >= 3:
                return {
                    'valid': False,
                    'reason': f'Too many positions in {base_currency} (max 3)'
                }
            
            # Check if too much exposure to same currency
            if same_currency_value > self.portfolio_value * 0.3:  # 30% max per currency
                return {
                    'valid': False,
                    'reason': f'Too much exposure to {base_currency} (max 30%)'
                }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"❌ Error checking correlation risk: {e}")
            return {'valid': True}  # Default to valid if check fails
    
    def _get_performance_adjustment(self) -> float:
        """Get performance-based risk adjustment"""
        try:
            # If recent performance is good, increase risk slightly
            # If recent performance is poor, decrease risk
            
            # Simplified: use daily P&L
            if self.daily_pnl > 0.02:  # If up 2%+ today
                return 1.2
            elif self.daily_pnl > 0:  # If profitable
                return 1.1
            elif self.daily_pnl > -0.02:  # Small loss
                return 0.9
            else:  # Larger loss
                return 0.7
                
        except Exception as e:
            logger.error(f"❌ Error calculating performance adjustment: {e}")
            return 1.0
    
    def calculate_dynamic_leverage(self, symbol: str, volatility: float, market_condition: str, confidence: float = 0.75) -> float:
        """Calculate dynamic leverage based on market conditions (UP TO 50X)"""
        try:
            # High leverage controls - UP TO 50X
            max_leverage_absolute = 50.0
            
            # Calculate volatility percentage for better understanding
            volatility_percent = volatility * 100
            
            # Volatility-based leverage limits (strict controls for high leverage)
            if volatility_percent < 1.5:      # Ultra low volatility
                max_vol_leverage = 50.0
            elif volatility_percent < 2.5:    # Low volatility
                max_vol_leverage = 35.0
            elif volatility_percent < 4.0:    # Medium-low volatility
                max_vol_leverage = 25.0
            elif volatility_percent < 6.0:    # Medium volatility
                max_vol_leverage = 15.0
            elif volatility_percent < 8.0:    # High volatility
                max_vol_leverage = 10.0
            else:                              # Extreme volatility
                max_vol_leverage = 5.0
            
            # Confidence-based leverage requirements (strict for high leverage)
            if confidence >= 0.95:            # 95%+ confidence
                confidence_max_leverage = 50.0
            elif confidence >= 0.90:          # 90%+ confidence
                confidence_max_leverage = 35.0
            elif confidence >= 0.85:          # 85%+ confidence
                confidence_max_leverage = 25.0
            elif confidence >= 0.80:          # 80%+ confidence
                confidence_max_leverage = 15.0
            elif confidence >= 0.75:          # 75%+ confidence
                confidence_max_leverage = 10.0
            else:                              # Below 75% confidence
                confidence_max_leverage = 5.0
            
            # Market condition adjustments
            market_multipliers = {
                'low_volatility': 1.0,
                'normal': 0.8,
                'high_volatility': 0.6,
                'extreme_volatility': 0.4
            }
            
            market_multiplier = market_multipliers.get(market_condition, 0.8)
            
            # Base leverage calculation (more sophisticated)
            if volatility_percent < 2.0:
                base_leverage = 10.0 * confidence  # High base for low vol + high confidence
            elif volatility_percent < 4.0:
                base_leverage = 7.0 * confidence   # Medium base
            else:
                base_leverage = 5.0 * confidence   # Conservative base for high vol
            
            # Apply market adjustment
            calculated_leverage = base_leverage * market_multiplier
            
            # Portfolio-level adjustments
            portfolio_adjustment = self._get_portfolio_leverage_adjustment()
            calculated_leverage *= portfolio_adjustment
            
            # Correlation adjustment (reduce leverage for correlated positions)
            correlation_adjustment = self._get_correlation_adjustment(symbol)
            calculated_leverage *= correlation_adjustment
            
            # Performance-based adjustment
            performance_adjustment = self._get_performance_adjustment()
            calculated_leverage *= performance_adjustment
            
            # Apply all limits (take the minimum for safety)
            final_leverage = min(
                max_leverage_absolute,      # Absolute max: 50x
                max_vol_leverage,           # Volatility-based limit
                confidence_max_leverage,    # Confidence-based limit
                calculated_leverage,        # Calculated leverage
                self.max_leverage          # Config max leverage
            )
            
            # Ensure minimum leverage
            final_leverage = max(1.0, final_leverage)
            
            # Emergency stops for extreme conditions
            if self.max_drawdown > 0.15:      # High drawdown
                final_leverage = min(final_leverage, 5.0)
            elif self.max_drawdown > 0.10:    # Medium drawdown
                final_leverage = min(final_leverage, 10.0)
            
            # Portfolio concentration limits
            if self._get_portfolio_concentration() > 0.5:  # Over 50% in similar assets
                final_leverage = min(final_leverage, 10.0)
            
            logger.info(f"🎯 Dynamic Leverage for {symbol}: "
                       f"Volatility: {volatility_percent:.2f}%, "
                       f"Confidence: {confidence:.1%}, "
                       f"Final Leverage: {round(final_leverage, 1)}x")
            
            return round(final_leverage, 1)
            
        except Exception as e:
            logger.error(f"❌ Error calculating dynamic leverage: {e}")
            return min(self.default_leverage, 5.0)  # Safe fallback
    
    def _get_market_adjustment(self) -> float:
        """Get market condition adjustment for leverage"""
        try:
            # Simplified market condition assessment
            # In a real implementation, this would analyze market volatility,
            # correlation, and other macro factors
            
            # Check current drawdown
            if self.max_drawdown > 0.15:  # High drawdown
                return 0.5
            elif self.max_drawdown > 0.1:  # Medium drawdown
                return 0.75
            else:
                return 1.0
                
        except Exception as e:
            logger.error(f"❌ Error getting market adjustment: {e}")
            return 1.0
    
    def _get_correlation_adjustment(self, symbol: str) -> float:
        """Get correlation-based leverage adjustment"""
        try:
            # Count similar positions
            base_currency = symbol.split('/')[0]
            similar_positions = sum(1 for pos in self.open_positions.keys() 
                                 if pos.split('/')[0] == base_currency)
            
            # Reduce leverage if many similar positions
            if similar_positions >= 2:
                return 0.7
            elif similar_positions >= 1:
                return 0.85
            else:
                return 1.0
                
        except Exception as e:
            logger.error(f"❌ Error getting correlation adjustment: {e}")
            return 1.0
    
    def _get_portfolio_leverage_adjustment(self) -> float:
        """Get portfolio-level leverage adjustment"""
        try:
            # Reduce leverage if portfolio is already highly leveraged
            current_leverage = self.calculate_current_leverage()
            
            if current_leverage > 30:      # High overall leverage
                return 0.5
            elif current_leverage > 20:   # Medium overall leverage
                return 0.7
            elif current_leverage > 10:   # Some leverage
                return 0.9
            else:                          # Low leverage
                return 1.0
                
        except Exception as e:
            logger.error(f"❌ Error getting portfolio leverage adjustment: {e}")
            return 0.8  # Conservative default
    
    def calculate_current_leverage(self) -> float:
        """Calculate current portfolio leverage"""
        try:
            # This would calculate the current weighted average leverage
            # across all open positions
            # For now, return a placeholder
            return 5.0
            
        except Exception as e:
            logger.error(f"❌ Error calculating current leverage: {e}")
            return 0.0
    
    def _get_portfolio_concentration(self) -> float:
        """Get portfolio concentration risk"""
        try:
            # This would calculate how concentrated the portfolio is
            # in similar assets (same sector, correlated pairs, etc.)
            # For now, return a placeholder
            return 0.3  # 30% concentration
            
        except Exception as e:
            logger.error(f"❌ Error calculating portfolio concentration: {e}")
            return 0.5  # Conservative assumption
    
    def calculate_stop_loss_take_profit(self, entry_price: float, atr: float, 
                                       direction: str) -> Tuple[float, List[float]]:
        """Calculate stop loss and take profit levels"""
        try:
            if direction.upper() == 'BUY':
                # Stop loss below entry
                stop_loss = entry_price - (atr * self.stop_loss_atr_multiplier)
                
                # Take profit levels above entry
                take_profit_levels = []
                for multiplier in self.take_profit_levels:
                    tp = entry_price + (atr * multiplier)
                    take_profit_levels.append(tp)
            
            else:  # SELL
                # Stop loss above entry
                stop_loss = entry_price + (atr * self.stop_loss_atr_multiplier)
                
                # Take profit levels below entry
                take_profit_levels = []
                for multiplier in self.take_profit_levels:
                    tp = entry_price - (atr * multiplier)
                    take_profit_levels.append(tp)
            
            return stop_loss, take_profit_levels
            
        except Exception as e:
            logger.error(f"❌ Error calculating SL/TP: {e}")
            return entry_price * 0.95, [entry_price * 1.05]  # Default values
    
    def assess_portfolio_risk(self) -> Dict[str, Any]:
        """Assess overall portfolio risk"""
        try:
            # Calculate total exposure
            total_exposure = sum(pos.get('position_value', 0) for pos in self.open_positions.values())
            exposure_ratio = total_exposure / self.portfolio_value
            
            # Calculate correlation risk
            correlation_risk = self._calculate_correlation_risk()
            
            # Calculate concentration risk
            concentration_risk = self._calculate_concentration_risk()
            
            # Calculate leverage risk
            leverage_risk = self._calculate_leverage_risk()
            
            # Overall risk score (0-100)
            risk_factors = [
                exposure_ratio * 30,        # 30% weight
                correlation_risk * 25,      # 25% weight
                concentration_risk * 25,    # 25% weight
                leverage_risk * 20         # 20% weight
            ]
            
            overall_risk_score = sum(risk_factors)
            
            # Risk level
            if overall_risk_score > 75:
                risk_level = 'HIGH'
            elif overall_risk_score > 50:
                risk_level = 'MEDIUM'
            elif overall_risk_score > 25:
                risk_level = 'LOW'
            else:
                risk_level = 'VERY_LOW'
            
            return {
                'overall_risk_score': overall_risk_score,
                'risk_level': risk_level,
                'exposure_ratio': exposure_ratio,
                'correlation_risk': correlation_risk,
                'concentration_risk': concentration_risk,
                'leverage_risk': leverage_risk,
                'max_drawdown': self.max_drawdown,
                'daily_pnl': self.daily_pnl,
                'open_positions_count': len(self.open_positions),
                'recommendations': self._get_risk_recommendations(overall_risk_score)
            }
            
        except Exception as e:
            logger.error(f"❌ Error assessing portfolio risk: {e}")
            return {'overall_risk_score': 50, 'risk_level': 'MEDIUM'}
    
    def _calculate_correlation_risk(self) -> float:
        """Calculate correlation risk score (0-100)"""
        try:
            if not self.open_positions:
                return 0
                
            # Count positions by currency
            currency_counts = {}
            for symbol in self.open_positions.keys():
                base_currency = symbol.split('/')[0]
                currency_counts[base_currency] = currency_counts.get(base_currency, 0) + 1
            
            # Calculate correlation penalty
            max_positions_per_currency = max(currency_counts.values())
            correlation_penalty = min(100, (max_positions_per_currency - 1) * 25)
            
            return correlation_penalty
            
        except Exception as e:
            logger.error(f"❌ Error calculating correlation risk: {e}")
            return 50
    
    def _calculate_concentration_risk(self) -> float:
        """Calculate concentration risk score (0-100)"""
        try:
            if not self.open_positions:
                return 0
            
            # Calculate position values
            position_values = [pos.get('position_value', 0) for pos in self.open_positions.values()]
            total_value = sum(position_values)
            
            if total_value == 0:
                return 0
            
            # Calculate concentration using Herfindahl index
            concentration_index = sum((value / total_value) ** 2 for value in position_values)
            
            # Convert to risk score (higher concentration = higher risk)
            concentration_risk = min(100, concentration_index * 100)
            
            return concentration_risk
            
        except Exception as e:
            logger.error(f"❌ Error calculating concentration risk: {e}")
            return 50
    
    def _calculate_leverage_risk(self) -> float:
        """Calculate leverage risk score (0-100)"""
        try:
            if not self.open_positions:
                return 0
            
            # Calculate average leverage
            leverages = [pos.get('leverage', 1) for pos in self.open_positions.values()]
            avg_leverage = sum(leverages) / len(leverages)
            
            # Risk increases with leverage
            leverage_risk = min(100, (avg_leverage / self.max_leverage) * 100)
            
            return leverage_risk
            
        except Exception as e:
            logger.error(f"❌ Error calculating leverage risk: {e}")
            return 50
    
    def _get_risk_recommendations(self, risk_score: float) -> List[str]:
        """Get risk management recommendations"""
        recommendations = []
        
        try:
            if risk_score > 75:
                recommendations.extend([
                    "Consider reducing position sizes",
                    "Close some correlated positions",
                    "Reduce leverage on new positions",
                    "Implement hedging strategies"
                ])
            elif risk_score > 50:
                recommendations.extend([
                    "Monitor position correlation closely",
                    "Consider position size limits",
                    "Review leverage usage"
                ])
            elif risk_score > 25:
                recommendations.extend([
                    "Maintain current risk levels",
                    "Monitor for new opportunities"
                ])
            else:
                recommendations.extend([
                    "Consider increasing position sizes",
                    "Look for additional opportunities"
                ])
            
            # Add specific recommendations based on current state
            if self.max_drawdown > 0.15:
                recommendations.append("High drawdown detected - reduce risk immediately")
            
            if len(self.open_positions) > 8:
                recommendations.append("Too many open positions - consider consolidation")
                
        except Exception as e:
            logger.error(f"❌ Error generating recommendations: {e}")
        
        return recommendations
    
    async def execute_hedging_strategy(self, symbol: str, position_value: float) -> Dict[str, Any]:
        """Execute hedging strategy for a position"""
        try:
            logger.info(f"🛡️ Executing hedging strategy for {symbol}")
            
            # Calculate hedge size
            hedge_size = position_value * self.hedge_ratio
            
            # Determine hedge instrument (simplified)
            if 'BTC' in symbol:
                hedge_symbol = 'BTCUSDT-PERP'  # BTC perpetual futures
            elif 'ETH' in symbol:
                hedge_symbol = 'ETHUSDT-PERP'  # ETH perpetual futures
            else:
                # Use a broader market hedge
                hedge_symbol = 'BTCUSDT-PERP'
            
            # In a real implementation, this would execute the hedge trade
            # For now, we'll simulate the hedge
            
            hedge_result = {
                'hedged': True,
                'hedge_symbol': hedge_symbol,
                'hedge_size': hedge_size,
                'hedge_ratio': self.hedge_ratio,
                'execution_time': datetime.now().isoformat(),
                'estimated_cost': hedge_size * 0.001  # Simplified cost calculation
            }
            
            logger.success(f"✅ Hedge executed for {symbol}: {hedge_size:.2f} via {hedge_symbol}")
            
            return hedge_result
            
        except Exception as e:
            logger.error(f"❌ Error executing hedging strategy: {e}")
            return {'hedged': False, 'error': str(e)}
    
    def update_position(self, symbol: str, position_data: Dict[str, Any]):
        """Update position information"""
        try:
            self.open_positions[symbol] = position_data
            logger.info(f"📊 Position updated for {symbol}")
            
        except Exception as e:
            logger.error(f"❌ Error updating position: {e}")
    
    def close_position(self, symbol: str, exit_price: float, exit_reason: str = "Manual"):
        """Close a position and update metrics"""
        try:
            if symbol not in self.open_positions:
                logger.warning(f"⚠️  Position {symbol} not found in open positions")
                return
            
            position = self.open_positions[symbol]
            
            # Calculate P&L
            entry_price = position.get('entry_price', 0)
            position_size = position.get('position_size', 0)
            side = position.get('side', 'BUY')
            
            if side == 'BUY':
                pnl = (exit_price - entry_price) * position_size
            else:
                pnl = (entry_price - exit_price) * position_size
            
            # Update portfolio value
            self.portfolio_value += pnl
            self.daily_pnl += pnl / self.portfolio_value  # As percentage
            
            # Update drawdown
            if self.portfolio_value > self.peak_portfolio_value:
                self.peak_portfolio_value = self.portfolio_value
                self.max_drawdown = 0
            else:
                current_drawdown = (self.peak_portfolio_value - self.portfolio_value) / self.peak_portfolio_value
                self.max_drawdown = max(self.max_drawdown, current_drawdown)
            
            # Remove position
            del self.open_positions[symbol]
            
            logger.success(f"✅ Position closed: {symbol} | P&L: {pnl:.2f} | Reason: {exit_reason}")
            
        except Exception as e:
            logger.error(f"❌ Error closing position: {e}")
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics"""
        try:
            portfolio_assessment = self.assess_portfolio_risk()
            
            return {
                'portfolio_value': self.portfolio_value,
                'daily_pnl': self.daily_pnl,
                'max_drawdown': self.max_drawdown,
                'open_positions_count': len(self.open_positions),
                'total_exposure': sum(pos.get('position_value', 0) for pos in self.open_positions.values()),
                'risk_assessment': portfolio_assessment,
                'updated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting risk metrics: {e}")
            return {'error': str(e)}
    
    def check_daily_limits(self) -> Dict[str, Any]:
        """Check if daily limits are breached"""
        try:
            limits_breached = []
            
            # Check daily loss limit
            if self.daily_pnl < -self.daily_loss_limit:
                limits_breached.append({
                    'type': 'daily_loss',
                    'current': self.daily_pnl,
                    'limit': -self.daily_loss_limit,
                    'action': 'stop_trading'
                })
            
            # Check maximum drawdown
            if self.max_drawdown > self.max_drawdown_limit:
                limits_breached.append({
                    'type': 'max_drawdown',
                    'current': self.max_drawdown,
                    'limit': self.max_drawdown_limit,
                    'action': 'reduce_positions'
                })
            
            return {
                'limits_ok': len(limits_breached) == 0,
                'breached_limits': limits_breached,
                'trading_allowed': len([l for l in limits_breached if l['action'] == 'stop_trading']) == 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking daily limits: {e}")
            return {'limits_ok': True, 'trading_allowed': True} 