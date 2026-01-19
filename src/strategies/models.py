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

    def to_html(self) -> str:
        """Formats the signal into a professional HTML message for Telegram."""
        side_emoji = "🚀" if self.direction in ['BUY', 'STRONG_BUY'] else "📉"
        header = f"🚨 <b>ULTRA SIGNAL: {self.symbol}</b> {side_emoji}"
        
        # Details
        body = (
            f"\n\n<b>Direction:</b> {self.direction}"
            f"\n<b>Confidence:</b> {self.confidence:.1%}"
            f"\n<b>Entry Price:</b> ${self.entry_price:.6f}"
            f"\n<b>Timeframe:</b> {self.timeframe}"
        )
        
        # Risk Management
        tp_str = ", ".join([f"${tp:.6f}" for tp in self.take_profit])
        risk = (
            f"\n\n🎯 <b>Targets:</b>"
            f"\nTP: {tp_str}"
            f"\nSL: ${self.stop_loss:.6f}"
            f"\nRR: {self.risk_reward:.2f}"
            f"\nSize: {self.position_size_pct:.1%}"
        )
        
        # Rationale
        ta = self.model_agreement.get('ta', 0.0)
        ml = self.model_agreement.get('ml', 0.0)
        sm = self.model_agreement.get('smart_money', 0.0)
        rationale = (
            f"\n\n🧠 <b>Analysis:</b>"
            f"\n- Technicals: {ta:.2f}"
            f"\n- AI Probability: {ml:.2f}"
            f"\n- Smart Money: {sm:+.2f}"
        )
        
        footer = f"\n\n<i>Generated at: {datetime.now().strftime('%H:%M:%S')}</i>"
        return header + body + risk + rationale + footer
