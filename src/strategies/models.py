from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional, List
from datetime import datetime

@dataclass
class MarketRegime:
    trend: str  # 'bullish', 'bearish', 'neutral'
    phase: str  # 'accumulation', 'distribution', 'markup', 'markdown'
    strength: float
    volatility: str # 'low', 'medium', 'high'
    volatility_value: float = 0.0
    crisis_mode: bool = False

@dataclass
class EnhancedSignal:
    symbol: str
    direction: str  # 'BUY', 'SELL', 'STRONG_BUY', 'STRONG_SELL', 'NEUTRAL'
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: Tuple[float, ...]
    position_size_pct: float
    expected_value: float
    risk_reward: float
    timeframe: str
    rationale: Dict
    valid_until: datetime
    model_agreement: Dict
    var_95: float
    max_drawdown_risk: float
    kelly_fraction: float
