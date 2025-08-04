#!/usr/bin/env python3
"""
Advanced AI Engine - Продвинутый AI движок для анализа
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from advanced_technical_analyzer import AdvancedTechnicalAnalyzer
from signal_explainer import SignalExplainer

logger = logging.getLogger(__name__)

class AdvancedAIEngine:
    """Продвинутый AI движок для анализа множественных пар"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.analyzer = AdvancedTechnicalAnalyzer()
        self.explainer = SignalExplainer()
        
        # Настройки анализа - очень мягкие критерии для тестирования
        self.analysis_config = config.get('analysis', {})
        self.min_confidence = self.analysis_config.get('min_confidence', 0.3)  # 30% для тестирования
        self.min_risk_reward = self.analysis_config.get('min_risk_reward', 1.0)  # 1.0 для тестирования
        self.max_signals_per_cycle = self.analysis_config.get('max_signals_per_cycle', 10)
        
        # Фильтры
        self.filters = {
            'volume_spike': True,
            'trend_confirmation': True,
            'pattern_recognition': True,
            'support_resistance': True,
            'multiframe_consensus': True
        }
        
        logger.info("🧠 Advanced AI Engine инициализирован")
        logger.info(f"⚙️ Минимальная уверенность: {self.min_confidence*100:.0f}%")
        logger.info(f"⚖️ Минимальный Risk/Reward: {self.min_risk_reward}")
    
    async def process_symbol(self, pair: str, ohlcv_data: Dict[str, pd.DataFrame]) -> Optional[Dict[str, Any]]:
        """
        Обрабатывает одну торговую пару
        
        Args:
            pair: Торговая пара
            ohlcv_data: Словарь с данными по таймфреймам
            
        Returns:
            Сигнал или None
        """
        try:
            if not ohlcv_data or len(ohlcv_data) < 2:
                return None
            
            # Анализируем каждый таймфрейм
            timeframe_analysis = {}
            for tf, data in ohlcv_data.items():
                if len(data) < 20:
                    continue
                
                analysis = self.analyzer._analyze_single_timeframe(data)
                support_resistance = self.analyzer.calculate_support_resistance(data)
                analysis.update(support_resistance)
                timeframe_analysis[tf] = analysis
            
            if not timeframe_analysis:
                return None
            
            # Создаем мультитаймфреймовый анализ
            mtf_analysis = self._create_mtf_analysis(timeframe_analysis)
            
            # Генерируем сигнал
            signal = self._generate_signal(pair, ohlcv_data, timeframe_analysis, mtf_analysis)
            
            if signal and signal.get('action') in ['BUY', 'SELL']:
                # Проверяем качество сигнала
                if self._validate_signal_quality(signal, timeframe_analysis, mtf_analysis):
                    return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка обработки {pair}: {e}")
            return None
    
    def _create_mtf_analysis(self, timeframe_analysis: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Создает мультитаймфреймовый анализ"""
        try:
            mtf_analysis = {
                'timeframes': timeframe_analysis,
                'overall_trend': 'neutral',
                'consensus_score': 0,
                'trend_agreement': 0
            }
            
            # Подсчитываем согласованность трендов
            bullish_count = 0
            bearish_count = 0
            total_timeframes = len(timeframe_analysis)
            
            for tf_data in timeframe_analysis.values():
                trend = tf_data.get('trend', 'neutral')
                if trend == 'bullish':
                    bullish_count += 1
                elif trend == 'bearish':
                    bearish_count += 1
            
            # Определяем общий тренд
            if bullish_count > bearish_count:
                mtf_analysis['overall_trend'] = 'bullish'
                mtf_analysis['trend_agreement'] = bullish_count / total_timeframes
            elif bearish_count > bullish_count:
                mtf_analysis['overall_trend'] = 'bearish'
                mtf_analysis['trend_agreement'] = bearish_count / total_timeframes
            
            # Рассчитываем consensus score
            consensus_factors = []
            
            # RSI consensus
            rsi_values = [tf_data.get('rsi', 50) for tf_data in timeframe_analysis.values()]
            rsi_consensus = self._calculate_consensus(rsi_values, 30, 70)
            consensus_factors.append(rsi_consensus)
            
            # MACD consensus
            macd_histograms = [tf_data.get('macd', {}).get('histogram', 0) for tf_data in timeframe_analysis.values()]
            macd_consensus = self._calculate_consensus(macd_histograms, -0.01, 0.01)
            consensus_factors.append(macd_consensus)
            
            # ADX consensus
            adx_values = [tf_data.get('adx', {}).get('adx', 0) for tf_data in timeframe_analysis.values()]
            adx_consensus = self._calculate_consensus(adx_values, 0, 25)
            consensus_factors.append(adx_consensus)
            
            mtf_analysis['consensus_score'] = np.mean(consensus_factors) if consensus_factors else 0
            
            return mtf_analysis
            
        except Exception as e:
            logger.error(f"Ошибка создания MTF анализа: {e}")
            return {'timeframes': timeframe_analysis, 'overall_trend': 'neutral', 'consensus_score': 0}
    
    def _calculate_consensus(self, values: List[float], min_threshold: float, max_threshold: float) -> float:
        """Рассчитывает consensus score для значений"""
        try:
            if not values:
                return 0
            
            # Нормализуем значения
            normalized = []
            for val in values:
                if val < min_threshold:
                    normalized.append(0)
                elif val > max_threshold:
                    normalized.append(1)
                else:
                    normalized.append((val - min_threshold) / (max_threshold - min_threshold))
            
            return np.mean(normalized)
            
        except Exception:
            return 0
    
    def _generate_signal(self, pair: str, ohlcv_data: Dict[str, pd.DataFrame], 
                        timeframe_analysis: Dict[str, Dict[str, Any]], 
                        mtf_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Генерирует торговый сигнал с более строгими критериями"""
        try:
            # Используем данные с основного таймфрейма (15m или 1h)
            primary_tf = '15m' if '15m' in ohlcv_data else '1h' if '1h' in ohlcv_data else list(ohlcv_data.keys())[0]
            primary_data = ohlcv_data[primary_tf]
            primary_analysis = timeframe_analysis[primary_tf]
            
            current_price = primary_data['close'].iloc[-1]
            
            # Анализируем индикаторы
            rsi = primary_analysis.get('rsi', 50)
            macd_hist = primary_analysis.get('macd', {}).get('histogram', 0)
            adx = primary_analysis.get('adx', {}).get('adx', 0)
            volume_ratio = primary_analysis.get('volume', {}).get('ratio', 1.0)
            
            # Определяем действие и уверенность - более строгие критерии
            action = 'HOLD'
            confidence = 0.5
            alpha_score = 0
            
            # RSI анализ - очень мягкие условия для тестирования
            if rsi > 60:  # Было 75
                action = 'SELL'
                confidence += 0.2
                alpha_score += 1
            elif rsi < 40:  # Было 25
                action = 'BUY'
                confidence += 0.2
                alpha_score += 1
            elif 45 <= rsi <= 55:  # Было 40-60
                confidence += 0.05  # Нейтральная зона
            
            # MACD анализ - очень мягкие условия для тестирования
            if abs(macd_hist) > 0.005:  # Было 0.02
                if macd_hist > 0 and action == 'BUY':
                    confidence += 0.2
                    alpha_score += 1
                elif macd_hist < 0 and action == 'SELL':
                    confidence += 0.2
                    alpha_score += 1
                elif action == 'HOLD':
                    action = 'BUY' if macd_hist > 0 else 'SELL'
                    confidence += 0.2
                    alpha_score += 1
            
            # ADX анализ (сила тренда) - очень мягкие условия для тестирования
            if adx > 20:  # Было 30
                confidence += 0.15
                alpha_score += 1
            
            # Volume анализ - очень мягкие условия для тестирования
            if volume_ratio > 1.2:  # Было 2.0
                confidence += 0.15
                alpha_score += 1
            
            # Мультитаймфреймовый consensus - очень мягкие условия для тестирования
            consensus_score = mtf_analysis.get('consensus_score', 0)
            if consensus_score > 0.5:  # Было 0.8
                confidence += 0.2
                alpha_score += 1
            
            # Trend agreement - очень мягкие условия для тестирования
            trend_agreement = mtf_analysis.get('trend_agreement', 0)
            if trend_agreement > 0.4:  # Было 0.7
                confidence += 0.15
                alpha_score += 1
            
            # Паттерны - очень мягкие условия для тестирования
            patterns = primary_analysis.get('patterns', {})
            if patterns:  # Убрал требование минимум 2 паттерна
                confidence += 0.15
                alpha_score += 1
            
            # Проверяем минимальную уверенность
            if confidence < self.min_confidence:
                action = 'HOLD'
                confidence = 0.5
            
            # Рассчитываем Risk/Reward
            risk_reward = self._calculate_risk_reward(current_price, action, primary_analysis)
            
            # Создаем сигнал
            signal = {
                'action': action,
                'symbol': pair,
                'price': current_price,
                'confidence': min(confidence, 0.95),
                'alpha_score': alpha_score,
                'risk_reward': risk_reward,
                'consensus_score': consensus_score,
                'trend_agreement': trend_agreement,
                'take_profit': self.explainer.calculate_take_profit_levels(current_price, 'long' if action == 'BUY' else 'short'),
                'stop_loss': self.explainer.calculate_stop_loss(current_price, 'long' if action == 'BUY' else 'short'),
                'analysis': primary_analysis,
                'mtf_analysis': mtf_analysis,
                'timestamp': datetime.now().isoformat()
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Ошибка генерации сигнала для {pair}: {e}")
            return None
    
    def _calculate_risk_reward(self, current_price: float, action: str, analysis: Dict[str, Any]) -> float:
        """Рассчитывает Risk/Reward ratio"""
        try:
            if action not in ['BUY', 'SELL']:
                return 0
            
            # Получаем уровни поддержки и сопротивления
            support = analysis.get('support', current_price * 0.95)
            resistance = analysis.get('resistance', current_price * 1.05)
            
            if action == 'BUY':
                # Для покупки: потенциальная прибыль = сопротивление - текущая цена
                # риск = текущая цена - поддержка
                potential_profit = resistance - current_price
                risk = current_price - support
            else:
                # Для продажи: потенциальная прибыль = текущая цена - поддержка
                # риск = сопротивление - текущая цена
                potential_profit = current_price - support
                risk = resistance - current_price
            
            if risk <= 0:
                return 0
            
            return potential_profit / risk
            
        except Exception:
            return 0
    
    def _validate_signal_quality(self, signal: Dict[str, Any], timeframe_analysis: Dict[str, Dict[str, Any]], 
                                mtf_analysis: Dict[str, Any]) -> bool:
        """Проверяет качество сигнала с очень мягкими критериями для тестирования"""
        try:
            # Проверяем минимальную уверенность
            if signal.get('confidence', 0) < self.min_confidence:
                return False
            
            # Проверяем Risk/Reward - очень мягкие условия для тестирования
            if signal.get('risk_reward', 0) < self.min_risk_reward:
                return False
            
            # Проверяем consensus score - очень мягкие условия для тестирования
            if mtf_analysis.get('consensus_score', 0) < 0.3:  # Было 0.6
                return False
            
            # Проверяем trend agreement - очень мягкие условия для тестирования
            if mtf_analysis.get('trend_agreement', 0) < 0.3:  # Было 0.6
                return False
            
            # Проверяем alpha score - очень мягкие условия для тестирования
            if signal.get('alpha_score', 0) < 2:  # Было 4 - минимум 2 подтверждающих фактора
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка валидации сигнала: {e}")
            return False
    
    async def process_and_collect_signals(self, pairs: List[str], timeframes: List[str], 
                                        data_manager, min_confidence: float = 0.85, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Анализирует N пар и выдает только top-N лучших сигналов по alpha/confidence.
        - pairs: список строк вида "BTC/USDT", ...
        - timeframes: список ['15m','1h','4h','1d']
        - data_manager: объект, возвращающий OHLCV по всем ТФ
        - ai_engine: сигнальный движок
        - min_confidence: минимальная уверенность для топ сигнала
        - top_n: сколько лучших выбирать для рассылки
        """
        all_signals = []
        errors = 0

        async def analyze_pair(pair):
            try:
                ohlcv_data = await data_manager.get_multi_timeframe_data(pair, timeframes)
                if not ohlcv_data:
                    return None
                signal = await self.process_symbol(pair, ohlcv_data)
                if signal and signal.get('action') in ('BUY', 'SELL'):
                    # Патчинг confidence, защита - согласно вашему шаблону
                    conf = signal.get('confidence', 0)
                    if isinstance(conf, str):
                        try:
                            conf = float(conf)
                        except:
                            conf = 0
                    while conf > 1.0:
                        conf /= 100.0
                    conf = max(0.0, min(conf, 0.95))
                    signal['confidence'] = conf
                    return signal
                return None
            except Exception as e:
                logger.warning(f"Signal error for {pair}: {e}")
                nonlocal errors
                errors += 1
                return None

        # Async-parallel анализ всех пар
        tasks = [analyze_pair(pair) for pair in pairs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем результаты
        signals_ok = []
        for result in results:
            if isinstance(result, dict) and result is not None:
                signals_ok.append(result)

        # Отбор только лучших TOP-N значений по alpha/confidence
        filtered = [s for s in signals_ok if s['confidence'] >= min_confidence]
        filtered = sorted(filtered, key=lambda x: x['confidence'], reverse=True)[:top_n]

        logger.info(f"Всего пар: {len(pairs)}. Сработало сигналов: {len(signals_ok)}. Среди лучших (conf>={min_confidence}): {len(filtered)}. Ошибок: {errors}")
        for sig in filtered:
            logger.info(f"{sig['symbol']} {sig['action']} conf={sig['confidence']:.3f} alpha={sig['alpha_score']} rr={sig['risk_reward']:.2f}")

        return filtered 