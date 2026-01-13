# src/strategies/smart_money_analyzer.py
"""
Smart Money Analyzer - детектор институциональных движений.
Анализ: Liquidity Sweeps, Funding Rates, Order Flow.
Data Source: Binance WebSocket (Primary), REST Fallback.
DefiLlama: DISABLED (using neutral fallback 0.95).
"""
import aiohttp
import logging
import numpy as np
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SmartMoneyAnalyzer:
    """
    Ан​ализатор "Умных денег" (институциональная ликвидность).
    Стратегия: Liquidity Sweeps + Funding Rate Contrairan.
    """
    def __init__(self, coinglass_key: str = "", hyblock_key: str = "", ws_client = None):
        self.coinglass_key = coinglass_key
        self.hyblock_key = hyblock_key
        self.ws_client = ws_client
        self.session = None
        
    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def get_liquidity_data(self, symbol: str) -> Dict:
        """
        [TEMPORARILY DISABLED] Возвращает нейтральные данные.
        """
        return self._get_mock_liquidity(symbol)

    def _get_mock_liquidity(self, symbol: str) -> Dict:
        """Фолбэк на мок-данные"""
        return {
            'total_long_liq_usd': 0.0,
            'total_short_liq_usd': 0.0,
            'liq_volume_ratio': 0.95, # Neutral/Slightly Bearish Fallback
            'is_mock': True
        }

    async def get_funding_metrics(self, symbol: str, exchange_connector=None) -> Dict:
        """
        Получает реальный Funding Rate и Open Interest.
        Приоритет: WebSocket -> REST API -> Mock.
        """
        # 1. Попытка получить из WebSocket (Real-time)
        if self.ws_client:
            ws_data = self.ws_client.get_metrics(symbol)
            if ws_data.get('is_ws'):
                return {
                    'current_funding': ws_data['funding_rate'],
                    'open_interest': ws_data['open_interest'],
                    'long_short_ratio': 1.0, 
                    'liq_ratio': ws_data['liq_ratio'],
                    'source': 'websocket',
                    'is_mock': False
                }

        # 2. Фолбэк на REST API
        if not exchange_connector:
            return self._get_mock_funding()

        try:
            raw_symbol = symbol.replace('/', '').replace(':', '')
            
            funding_data = await exchange_connector.fapiPublicGetFundingRate({
                'symbol': raw_symbol,
                'limit': 1
            })
            current_funding = float(funding_data[0]['fundingRate']) if funding_data else 0.0
            
            oi_data = await exchange_connector.fapiPublicGetOpenInterest({
                'symbol': raw_symbol
            })
            open_interest = float(oi_data['openInterest']) if oi_data else 0.0
            
            return {
                'current_funding': current_funding,
                'open_interest': open_interest,
                'long_short_ratio': 1.0,
                'source': 'rest_api',
                'is_mock': False
            }
        except Exception as e:
            logger.error(f"Error fetching REST metrics for {symbol}: {e}")
            return self._get_mock_funding()

    def _get_mock_funding(self) -> Dict:
        return {
            'current_funding': 0.0,
            'open_interest': 0.0,
            'long_short_ratio': 1.0,
            'funding_trend': 'stable',
            'is_mock': True
        }

    async def analyze_smart_money_context(
        self,
        symbol: str,
        current_price: float,
        direction: str,
        exchange_connector = None
    ) -> Dict:
        """
        Главная функция: определяет Smart Money boost для сигнала.
        DYNAMIC SCORING: адаптируется к экстремальным условиям.
        """
        liq_data = await self.get_liquidity_data(symbol)
        fund_data = await self.get_funding_metrics(symbol, exchange_connector)
        
        score_boost = 0.0
        rationale = {}
        
        # === 1. DYNAMIC LIQUIDITY ANALYSIS ===
        liq_ratio = liq_data.get('liq_volume_ratio', 1.0)
        
        # Extreme imbalance (3x+): Strong signal
        if liq_ratio > 3.0 and direction == 'BUY':
            score_boost += 0.20
            rationale['liquidity'] = 'EXTREME_SHORT_SQUEEZE_POTENTIAL'
        elif liq_ratio < 0.33 and direction == 'SELL':
            score_boost += 0.20
            rationale['liquidity'] = 'EXTREME_LONG_LIQUIDATION_POTENTIAL'
        # Moderate imbalance (2x): Medium signal
        elif liq_ratio > 2.0 and direction == 'BUY':
            score_boost += 0.10
            rationale['liquidity'] = 'HIGH_SHORT_LIQUIDATION_POTENTIAL'
        elif liq_ratio < 0.5 and direction == 'SELL':
            score_boost += 0.10
            rationale['liquidity'] = 'HIGH_LONG_LIQUIDATION_POTENTIAL'
            
        # === 2. DYNAMIC FUNDING RATE ANALYSIS ===
        funding = fund_data.get('current_funding', 0)
        
        # Extreme funding (>1% or <-1%): Very strong contrarian signal
        if funding > 0.01 and direction == 'SELL':
            score_boost += 0.15
            rationale['funding'] = 'EXTREME_OVERBOUGHT_FUNDING'
        elif funding < -0.01 and direction == 'BUY':
            score_boost += 0.15
            rationale['funding'] = 'EXTREME_OVERSOLD_FUNDING'
        # Moderate funding (>0.03% or <-0.03%): Medium contrarian signal
        elif funding > 0.0003 and direction == 'SELL':
            score_boost += 0.08
            rationale['funding'] = 'MODERATE_OVERBOUGHT_FUNDING'
        elif funding < -0.0003 and direction == 'BUY':
            score_boost += 0.08
            rationale['funding'] = 'MODERATE_OVERSOLD_FUNDING'
        # Slight funding (>0.01% or <-0.01%): Weak contrarian signal
        elif funding > 0.0001 and direction == 'SELL':
            score_boost += 0.03
            rationale['funding'] = 'SLIGHT_OVERBOUGHT_FUNDING'
        elif funding < -0.0001 and direction == 'BUY':
            score_boost += 0.03
            rationale['funding'] = 'SLIGHT_OVERSOLD_FUNDING'

        return {
            'smart_money_boost': min(0.30, max(-0.10, score_boost)),
            'rationale': rationale,
            'metrics': {
                'funding_rate': funding,
                'liq_ratio': liq_ratio,
                'is_real_data': fund_data.get('source') == 'websocket',
                'source': fund_data.get('source', 'rest')
            }
        }

    async def close(self):
        """Cleanup aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
