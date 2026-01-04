import json
import logging
import asyncio
import google.generativeai as genai
from typing import Dict, Optional, List
from src.core.settings import settings
from src.strategies.models import MarketRegime, EnhancedSignal
from src.strategies.onchain_analyzer import OnChainData

logger = logging.getLogger(__name__)

class AdvancedNeuralCore:
    """
    Institutional-grade neural synthesis core.
    Ported from QuantAI Alpha (TypeScript) to Python.
    """
    
    def __init__(self):
        if settings.gemini_api_key and settings.gemini_api_key != 'ВАШ_GEMINI_API_KEY':
            genai.configure(api_key=settings.gemini_api_key)
            # Using latest stable or preview model as per TS ('gemini-3-pro-preview' interpreted as gemini-1.5-pro or similar)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            self.enabled = True
        else:
            self.enabled = False
            logger.warning("Gemini API Key not set. AI Engine will be disabled.")

    async def process_signal(self, 
                             symbol: str, 
                             ohlcv_data: Dict, 
                             regime: MarketRegime, 
                             indicators: Dict, 
                             onchain: OnChainData,
                             features: Dict) -> Optional[Dict]:
        """
        Synthesizes multiple data streams into a final decision using Gemini.
        """
        if not self.enabled:
            return None

        prompt = f"""
        Act as an institutional-grade crypto quantitative analysis agent (QuantAI).
        Perform a deep-dive neural scan for {symbol}.
        
        [CONTEXT DATA]
        Market Regime: {regime.__dict__}
        Technical Indicators (last values): {{k: v.iloc[-1] if hasattr(v, 'iloc') else v for k, v in indicators.items()}}
        Alpha Features: {features}
        On-Chain Data: {onchain.__dict__}
        
        [ON-CHAIN METRICS INTERPRETATION GUIDE]
        - exchangeNetFlow: Large negative values (outflows) are highly bullish (accumulation). Large positive values are bearish (distribution).
        - whaleTransactionCount: High spikes often precede volatility or institutional positioning.
        - mvrvRatio: Below 1.0 is deep value, above 3.0 is a potential local top/overvaluation.
        
        [REQUIREMENTS]
        1. Determine Signal Direction (STRONG_BUY, BUY, NEUTRAL, SELL, STRONG_SELL).
        2. MTF ALIGNMENT: Breakdown alignment across 15m, 1h, and 4h timeframes.
        3. ML MODEL CONSENSUS: Critically evaluate agreement between TA and current regime. 
           Reconcile technical signals with on-chain health. If they conflict (e.g. Bullish TA but Net Inflow to exchanges), reduce confidence and explain why.
        4. ON-CHAIN VERDICT: Specifically interpret the exchange flows and whale count. Is this "smart money" accumulation?
        5. ON-CHAIN SCORE: Generate a score from 0.0 to 1.0.
        6. Calculate Kelly Criterion fraction (0.0 to 0.25) based on R:R and Confidence.
        
        [RESPONSE FORMAT]
        You MUST respond in strict JSON format matching this schema:
        {{
            "direction": "STRING",
            "confidence": NUMBER (0.0 to 1.0),
            "onChainScore": NUMBER (0.0 to 1.0),
            "mlScore": NUMBER (0.0 to 1.0),
            "mtfAlignmentScore": NUMBER (0.0 to 1.0),
            "kellyFraction": NUMBER (0.0 to 0.25),
            "rationale": {{
                "summary": "STRING",
                "technicalAnalysis": "STRING",
                "mlInsights": "STRING",
                "onChainDeepDive": "STRING",
                "mtfDetails": "STRING"
            }}
        }}
        """

        try:
            # Wrap Gemini call in asyncio-friendly way if needed, though genai is blocking
            # Generating in a thread to avoid blocking event loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            ))
            
            result = json.loads(response.text)
            return result
            
        except Exception as e:
            logger.error(f"AI Neural Core Error for {symbol}: {e}")
            return None
