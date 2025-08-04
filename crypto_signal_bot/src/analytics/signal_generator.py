"""
Signal Generator for CryptoAlphaPro
Generates trading signals using technical analysis and ML predictions
"""

import asyncio
import pandas as pd
import numpy as np
import talib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from loguru import logger
import json

from src.config.config_manager import ConfigManager
from src.data_collector.data_manager import DataManager
from src.prediction.ml_predictor import MLPredictor
from src.analytics.technical_indicators import TechnicalIndicators
from src.analytics.multi_timeframe_analyzer import MultiTimeframeAnalyzer


class SignalGenerator:
    """Main signal generation class"""
    
    def __init__(self, config: ConfigManager, data_manager: DataManager, ml_predictor: MLPredictor):
        self.config = config
        self.data_manager = data_manager
        self.ml_predictor = ml_predictor
        self.technical_indicators = TechnicalIndicators(config)
        self.multi_timeframe = MultiTimeframeAnalyzer(config)
        
        self.running = False
        self.signal_tasks: List[asyncio.Task] = []
        self.latest_signals: Dict[str, dict] = {}
        
        # Configuration
        self.trading_pairs = config.get_trading_pairs()
        self.timeframes = config.get_timeframes()
        self.confidence_threshold = config.get('signals.confidence_threshold', 0.7)
        
    async def start_signal_generation(self):
        """Start signal generation process"""
        self.running = True
        
        try:
            logger.info("🎯 Starting signal generation...")
            
            # Start signal generation for each pair
            for pair in self.trading_pairs:
                task = asyncio.create_task(
                    self._generate_signals_for_pair(pair),
                    name=f"signals_{pair.replace('/', '_')}"
                )
                self.signal_tasks.append(task)
            
            # Start signal monitoring task
            monitor_task = asyncio.create_task(
                self._monitor_signals(),
                name="signal_monitoring"
            )
            self.signal_tasks.append(monitor_task)
            
            logger.info(f"✅ Started signal generation for {len(self.trading_pairs)} pairs")
            
            # Wait for all tasks
            await asyncio.gather(*self.signal_tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ Error in signal generation: {e}")
            raise
    
    async def _generate_signals_for_pair(self, pair: str):
        """Generate signals for a specific trading pair"""
        while self.running:
            try:
                # Get the best exchange for this pair
                best_exchange = await self._find_best_exchange(pair)
                if not best_exchange:
                    await asyncio.sleep(60)
                    continue
                
                # Perform multi-timeframe analysis
                mtf_analysis = await self._multi_timeframe_analysis(best_exchange, pair)
                if not mtf_analysis:
                    await asyncio.sleep(30)
                    continue
                
                # Get ML predictions
                ml_predictions = await self._get_ml_predictions(best_exchange, pair)
                
                # Generate signal
                signal = await self._generate_signal(
                    pair=pair,
                    exchange=best_exchange,
                    mtf_analysis=mtf_analysis,
                    ml_predictions=ml_predictions
                )
                
                if signal and signal['confidence'] >= self.confidence_threshold:
                    # Store and broadcast signal
                    await self._process_new_signal(signal)
                
                # Wait before next analysis (based on shortest timeframe)
                await asyncio.sleep(self._get_update_interval())
                
            except Exception as e:
                logger.error(f"❌ Error generating signals for {pair}: {e}")
                await asyncio.sleep(60)
    
    async def _multi_timeframe_analysis(self, exchange: str, pair: str) -> Optional[Dict]:
        """Perform multi-timeframe technical analysis"""
        try:
            analysis_results = {}
            
            for timeframe in self.timeframes:
                # Get historical data
                end_time = datetime.now()
                start_time = end_time - timedelta(days=30)  # 30 days of data
                
                data = await self.data_manager.get_historical_data(
                    exchange, pair, timeframe, start_time, end_time
                )
                
                if data is None or len(data) < 50:
                    continue
                
                # Calculate technical indicators
                indicators = await self._calculate_indicators(data)
                
                # Determine trend
                trend = await self._determine_trend(data, indicators)
                
                # Calculate signal strength
                strength = await self._calculate_signal_strength(indicators, trend)
                
                analysis_results[timeframe] = {
                    'trend': trend,
                    'strength': strength,
                    'indicators': indicators,
                    'last_price': float(data['close'].iloc[-1]),
                    'volume_change': self._calculate_volume_change(data)
                }
            
            if not analysis_results:
                return None
            
            # Aggregate multi-timeframe consensus
            consensus = self._calculate_mtf_consensus(analysis_results)
            
            return {
                'timeframes': analysis_results,
                'consensus': consensus,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error in multi-timeframe analysis: {e}")
            return None
    
    async def _calculate_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators"""
        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            volume = data['volume'].values
            
            # Get indicator configurations
            rsi_config = self.config.get('indicators.rsi')
            macd_config = self.config.get('indicators.macd')
            ema_config = self.config.get('indicators.ema')
            atr_config = self.config.get('indicators.atr')
            
            indicators = {}
            
            # RSI
            if len(close) >= rsi_config['period']:
                indicators['rsi'] = float(talib.RSI(close, timeperiod=rsi_config['period'])[-1])
            
            # MACD
            if len(close) >= macd_config['slow_period']:
                macd, macdsignal, macdhist = talib.MACD(
                    close,
                    fastperiod=macd_config['fast_period'],
                    slowperiod=macd_config['slow_period'],
                    signalperiod=macd_config['signal_period']
                )
                indicators['macd'] = {
                    'macd': float(macd[-1]) if not np.isnan(macd[-1]) else 0,
                    'signal': float(macdsignal[-1]) if not np.isnan(macdsignal[-1]) else 0,
                    'histogram': float(macdhist[-1]) if not np.isnan(macdhist[-1]) else 0
                }
            
            # EMAs
            if len(close) >= ema_config['long_period']:
                indicators['ema_short'] = float(talib.EMA(close, timeperiod=ema_config['short_period'])[-1])
                indicators['ema_long'] = float(talib.EMA(close, timeperiod=ema_config['long_period'])[-1])
            
            # ATR
            if len(close) >= atr_config['period']:
                indicators['atr'] = float(talib.ATR(high, low, close, timeperiod=atr_config['period'])[-1])
            
            # Bollinger Bands
            if len(close) >= 20:
                upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
                indicators['bb'] = {
                    'upper': float(upper[-1]),
                    'middle': float(middle[-1]),
                    'lower': float(lower[-1]),
                    'position': (close[-1] - lower[-1]) / (upper[-1] - lower[-1])
                }
            
            # Volume indicators
            if len(volume) >= 20:
                volume_sma = talib.SMA(volume, timeperiod=20)
                indicators['volume_ratio'] = float(volume[-1] / volume_sma[-1]) if volume_sma[-1] > 0 else 1
            
            # Stochastic
            if len(close) >= 14:
                slowk, slowd = talib.STOCH(high, low, close, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
                indicators['stoch'] = {
                    'k': float(slowk[-1]) if not np.isnan(slowk[-1]) else 50,
                    'd': float(slowd[-1]) if not np.isnan(slowd[-1]) else 50
                }
            
            return indicators
            
        except Exception as e:
            logger.error(f"❌ Error calculating indicators: {e}")
            return {}
    
    async def _determine_trend(self, data: pd.DataFrame, indicators: Dict) -> str:
        """Determine trend direction"""
        try:
            trend_signals = []
            
            # EMA trend
            if 'ema_short' in indicators and 'ema_long' in indicators:
                if indicators['ema_short'] > indicators['ema_long']:
                    trend_signals.append('bullish')
                else:
                    trend_signals.append('bearish')
            
            # MACD trend
            if 'macd' in indicators:
                macd_data = indicators['macd']
                if macd_data['histogram'] > 0:
                    trend_signals.append('bullish')
                else:
                    trend_signals.append('bearish')
            
            # Price action trend
            close = data['close'].values
            if len(close) >= 20:
                sma_20 = talib.SMA(close, timeperiod=20)[-1]
                if close[-1] > sma_20:
                    trend_signals.append('bullish')
                else:
                    trend_signals.append('bearish')
            
            # Count trend signals
            bullish_count = trend_signals.count('bullish')
            bearish_count = trend_signals.count('bearish')
            
            if bullish_count > bearish_count:
                return 'bullish'
            elif bearish_count > bullish_count:
                return 'bearish'
            else:
                return 'neutral'
                
        except Exception as e:
            logger.error(f"❌ Error determining trend: {e}")
            return 'neutral'
    
    async def _calculate_signal_strength(self, indicators: Dict, trend: str) -> float:
        """Calculate signal strength (0-1)"""
        try:
            strength_factors = []
            
            # RSI strength
            if 'rsi' in indicators:
                rsi = indicators['rsi']
                if trend == 'bullish' and 55 <= rsi <= 80:
                    strength_factors.append(0.8)
                elif trend == 'bearish' and 20 <= rsi <= 45:
                    strength_factors.append(0.8)
                elif rsi > 80 or rsi < 20:
                    strength_factors.append(0.3)  # Overbought/oversold
                else:
                    strength_factors.append(0.5)
            
            # MACD strength
            if 'macd' in indicators:
                macd_data = indicators['macd']
                if trend == 'bullish' and macd_data['histogram'] > 0:
                    strength_factors.append(0.9)
                elif trend == 'bearish' and macd_data['histogram'] < 0:
                    strength_factors.append(0.9)
                else:
                    strength_factors.append(0.4)
            
            # Volume strength
            if 'volume_ratio' in indicators:
                vol_ratio = indicators['volume_ratio']
                if vol_ratio > 1.5:
                    strength_factors.append(0.9)
                elif vol_ratio > 1.2:
                    strength_factors.append(0.7)
                else:
                    strength_factors.append(0.5)
            
            # Bollinger Bands position
            if 'bb' in indicators:
                bb_pos = indicators['bb']['position']
                if trend == 'bullish' and 0.3 <= bb_pos <= 0.8:
                    strength_factors.append(0.8)
                elif trend == 'bearish' and 0.2 <= bb_pos <= 0.7:
                    strength_factors.append(0.8)
                else:
                    strength_factors.append(0.4)
            
            return np.mean(strength_factors) if strength_factors else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error calculating signal strength: {e}")
            return 0.5
    
    def _calculate_volume_change(self, data: pd.DataFrame) -> float:
        """Calculate volume change percentage"""
        try:
            if len(data) < 2:
                return 0.0
            
            current_volume = data['volume'].iloc[-1]
            previous_volume = data['volume'].iloc[-2]
            
            if previous_volume > 0:
                return (current_volume - previous_volume) / previous_volume
            return 0.0
            
        except:
            return 0.0
    
    def _calculate_mtf_consensus(self, analysis_results: Dict) -> Dict:
        """Calculate multi-timeframe consensus"""
        try:
            trends = []
            strengths = []
            
            # Weight timeframes (longer timeframes have more weight)
            timeframe_weights = {
                '15m': 0.1,
                '1h': 0.2,
                '4h': 0.3,
                '1d': 0.4
            }
            
            weighted_bullish = 0
            weighted_bearish = 0
            total_weight = 0
            
            for tf, result in analysis_results.items():
                weight = timeframe_weights.get(tf, 0.1)
                strength = result['strength']
                
                if result['trend'] == 'bullish':
                    weighted_bullish += weight * strength
                elif result['trend'] == 'bearish':
                    weighted_bearish += weight * strength
                
                total_weight += weight
                strengths.append(strength)
            
            # Determine consensus
            if weighted_bullish > weighted_bearish:
                consensus_trend = 'bullish'
                consensus_strength = weighted_bullish / total_weight if total_weight > 0 else 0
            elif weighted_bearish > weighted_bullish:
                consensus_trend = 'bearish'
                consensus_strength = weighted_bearish / total_weight if total_weight > 0 else 0
            else:
                consensus_trend = 'neutral'
                consensus_strength = np.mean(strengths) if strengths else 0
            
            # Determine consensus level
            if consensus_strength > 0.8:
                consensus_level = 'strong'
            elif consensus_strength > 0.6:
                consensus_level = 'moderate'
            else:
                consensus_level = 'weak'
            
            return {
                'trend': consensus_trend,
                'strength': consensus_strength,
                'level': consensus_level,
                'timeframe_agreement': len([r for r in analysis_results.values() if r['trend'] == consensus_trend]) / len(analysis_results)
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculating MTF consensus: {e}")
            return {'trend': 'neutral', 'strength': 0.5, 'level': 'weak', 'timeframe_agreement': 0}
    
    async def _get_ml_predictions(self, exchange: str, pair: str) -> Optional[Dict]:
        """Get ML model predictions"""
        try:
            if not self.ml_predictor:
                return None
                
            # Get prediction from ML models
            prediction = await self.ml_predictor.predict(exchange, pair)
            return prediction
            
        except Exception as e:
            logger.error(f"❌ Error getting ML predictions: {e}")
            return None
    
    async def _generate_signal(self, pair: str, exchange: str, mtf_analysis: Dict, 
                              ml_predictions: Optional[Dict]) -> Optional[Dict]:
        """Generate final trading signal"""
        try:
            consensus = mtf_analysis['consensus']
            
            # Check if signal meets minimum criteria
            if consensus['strength'] < 0.5 or consensus['trend'] == 'neutral':
                return None
            
            # Get current price and ATR for risk calculations
            current_price = None
            atr_value = None
            
            for tf_data in mtf_analysis['timeframes'].values():
                if current_price is None:
                    current_price = tf_data['last_price']
                if 'atr' in tf_data['indicators']:
                    atr_value = tf_data['indicators']['atr']
                    break
            
            if not current_price or not atr_value:
                return None
            
            # Calculate entry, stop loss, and take profit levels
            entry_range, stop_loss, take_profit_levels = self._calculate_levels(
                current_price, atr_value, consensus['trend']
            )
            
            # Calculate leverage based on volatility
            leverage = self._calculate_leverage(atr_value, current_price)
            
            # Combine technical and ML confidence
            technical_confidence = consensus['strength']
            ml_confidence = ml_predictions.get('confidence', 0.5) if ml_predictions else 0.5
            
            # Weighted average (70% technical, 30% ML)
            final_confidence = 0.7 * technical_confidence + 0.3 * ml_confidence
            
            # Create signal
            signal = {
                'symbol': pair,
                'exchange': exchange,
                'action': 'BUY' if consensus['trend'] == 'bullish' else 'SELL',
                'entry_range': entry_range,
                'stop_loss': stop_loss,
                'take_profit': take_profit_levels,
                'leverage': leverage,
                'confidence': final_confidence,
                'indicators': self._extract_key_indicators(mtf_analysis),
                'timestamp': datetime.now().isoformat(),
                'analysis': {
                    'trend_strength': consensus['level'],
                    'timeframe_agreement': consensus['timeframe_agreement'],
                    'ml_prediction': ml_predictions.get('direction') if ml_predictions else None
                }
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Error generating signal: {e}")
            return None
    
    def _calculate_levels(self, price: float, atr: float, trend: str) -> Tuple[List[float], float, List[float]]:
        """Calculate entry, stop loss, and take profit levels"""
        risk_config = self.config.get_risk_config()
        
        if trend == 'bullish':
            # Entry range (slightly above current price)
            entry_low = price * 0.999
            entry_high = price * 1.001
            entry_range = [entry_low, entry_high]
            
            # Stop loss below entry
            stop_loss = price - (atr * risk_config.stop_loss_atr_multiplier)
            
            # Take profit levels
            take_profit_levels = []
            for multiplier in risk_config.take_profit_levels:
                tp = price + (atr * multiplier)
                take_profit_levels.append(tp)
        
        else:  # bearish
            # Entry range (slightly below current price)
            entry_high = price * 1.001
            entry_low = price * 0.999
            entry_range = [entry_low, entry_high]
            
            # Stop loss above entry
            stop_loss = price + (atr * risk_config.stop_loss_atr_multiplier)
            
            # Take profit levels
            take_profit_levels = []
            for multiplier in risk_config.take_profit_levels:
                tp = price - (atr * multiplier)
                take_profit_levels.append(tp)
        
        return entry_range, stop_loss, take_profit_levels
    
    def _calculate_leverage(self, atr: float, price: float) -> float:
        """Calculate appropriate leverage based on volatility"""
        risk_config = self.config.get_risk_config()
        
        # Calculate volatility percentage
        volatility = (atr / price) if price > 0 else 0.05
        
        # Determine market condition
        if volatility > risk_config.volatility_thresholds['high']:
            market_condition = 'high_volatility'
        elif volatility > risk_config.volatility_thresholds['normal']:
            market_condition = 'normal'
        else:
            market_condition = 'low_volatility'
        
        # Base leverage factors
        base_factors = {
            'high_volatility': 0.03,
            'normal': 0.05,
            'low_volatility': 0.08
        }
        
        # Calculate leverage
        base_factor = base_factors[market_condition]
        calculated_leverage = min(risk_config.max_leverage, 1.0 / (volatility * base_factor))
        
        return round(calculated_leverage, 1)
    
    def _extract_key_indicators(self, mtf_analysis: Dict) -> Dict:
        """Extract key indicators for signal display"""
        try:
            # Use 1h timeframe as base, fallback to available timeframes
            base_tf = None
            for tf in ['1h', '4h', '15m', '1d']:
                if tf in mtf_analysis['timeframes']:
                    base_tf = mtf_analysis['timeframes'][tf]
                    break
            
            if not base_tf:
                return {}
            
            indicators = base_tf['indicators']
            
            return {
                'rsi': round(indicators.get('rsi', 50), 1),
                'volume_change': f"{base_tf['volume_change']*100:+.1f}%",
                'trend_strength': mtf_analysis['consensus']['level'],
                'volatility_index': round((indicators.get('atr', 0) / base_tf['last_price']) * 100, 1) if base_tf['last_price'] > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error extracting indicators: {e}")
            return {}
    
    async def _process_new_signal(self, signal: Dict):
        """Process and store new signal"""
        try:
            pair = signal['symbol']
            
            # Store latest signal
            self.latest_signals[pair] = signal
            
            # Log signal
            logger.success(f"🎯 New {signal['action']} signal for {pair} | "
                          f"Confidence: {signal['confidence']:.2f} | "
                          f"Leverage: {signal['leverage']}x")
            
            # TODO: Send to Telegram bot
            # TODO: Store in database
            # TODO: Trigger risk management checks
            
        except Exception as e:
            logger.error(f"❌ Error processing signal: {e}")
    
    async def _find_best_exchange(self, pair: str) -> Optional[str]:
        """Find the best exchange for a trading pair based on volume and spread"""
        try:
            # For now, return the first available exchange
            # TODO: Implement proper exchange selection logic
            for exchange_name in self.data_manager.exchanges.keys():
                return exchange_name
            return None
            
        except Exception as e:
            logger.error(f"❌ Error finding best exchange: {e}")
            return None
    
    def _get_update_interval(self) -> int:
        """Get update interval based on shortest timeframe"""
        timeframe_seconds = {
            '15m': 900,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }
        
        shortest_tf = min(self.timeframes, key=lambda tf: timeframe_seconds.get(tf, 3600))
        base_interval = timeframe_seconds.get(shortest_tf, 3600)
        
        # Update every 1/10th of the shortest timeframe, minimum 30 seconds
        return max(30, base_interval // 10)
    
    async def _monitor_signals(self):
        """Monitor and manage active signals"""
        while self.running:
            try:
                # Check for signal updates, expired signals, etc.
                current_time = datetime.now()
                
                for pair, signal in list(self.latest_signals.items()):
                    signal_time = datetime.fromisoformat(signal['timestamp'])
                    
                    # Remove old signals (older than 1 hour)
                    if (current_time - signal_time).seconds > 3600:
                        del self.latest_signals[pair]
                        logger.info(f"🗑️  Removed expired signal for {pair}")
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"❌ Error in signal monitoring: {e}")
                await asyncio.sleep(300)
    
    def get_latest_signals(self) -> Dict[str, dict]:
        """Get all latest signals"""
        return self.latest_signals.copy()
    
    async def get_signal_for_pair(self, pair: str) -> Optional[Dict]:
        """Get latest signal for specific pair"""
        return self.latest_signals.get(pair)
    
    async def shutdown(self):
        """Shutdown signal generation"""
        logger.info("🛑 Shutting down Signal Generator...")
        self.running = False
        
        # Cancel all tasks
        for task in self.signal_tasks:
            if not task.done():
                task.cancel()
        
        logger.success("✅ Signal Generator shutdown completed") 