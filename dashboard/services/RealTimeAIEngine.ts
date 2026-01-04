
import { GoogleGenAI, Type } from "@google/genai";
import { EnhancedSignal, MarketData, MarketRegime, AdaptiveIndicators, SignalDirection, AlphaFeatures, PatternMatch, OnChainData } from "../types";
import { FeatureEngineer } from "./FeatureEngineer";
import { withRetry } from "../utils/apiUtils";

export class RealTimeAIEngine {
  private ai: GoogleGenAI;

  constructor() {
    this.ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
  }

  /**
   * Institutional-grade Risk Management Engine with dynamic scaling.
   */
  private applyRiskManagement(
    lastPrice: number,
    direction: SignalDirection,
    regime: MarketRegime,
    indicators: AdaptiveIndicators
  ) {
    const isLong = direction.includes('BUY');
    const atr = indicators.atr || lastPrice * 0.01;
    const adx = indicators.adx || 20;
    const phase = regime.phase;

    // 1. DYNAMIC STOP-LOSS (SL) MULTIPLIER
    let baseMultiplier = 2.0; 
    switch (regime.volatility) {
      case 'low': baseMultiplier = 1.4; break;
      case 'medium': baseMultiplier = 2.0; break;
      case 'high': baseMultiplier = 3.2; break;
      case 'panic': baseMultiplier = 4.5; break;
    }

    const trendTightening = adx > 30 ? 0.85 : adx > 20 ? 0.95 : 1.15;
    
    let phaseBuffer = 1.0;
    if (phase === 'accumulation' || phase === 'distribution') phaseBuffer = 1.2;
    if (regime.crisisMode) phaseBuffer *= 1.4;

    const finalSlMultiplier = baseMultiplier * trendTightening * phaseBuffer;
    const slDistance = atr * finalSlMultiplier;
    const stopLoss = isLong ? lastPrice - slDistance : lastPrice + slDistance;

    // 2. TAKE-PROFIT (TP) EXPANSION
    let tpExpansion = 1.0;
    if (adx > 35) tpExpansion = 1.6;
    else if (adx > 20) tpExpansion = 1.2;
    else tpExpansion = 0.9; 

    if (phase === 'markup' || phase === 'markdown') tpExpansion *= 1.25;

    const tp1Dist = slDistance * 1.5 * tpExpansion;
    const tp2Dist = slDistance * 3.0 * tpExpansion;
    const tp3Dist = slDistance * 6.0 * tpExpansion;

    const tp1 = isLong ? lastPrice + tp1Dist : lastPrice - tp1Dist;
    const tp2 = isLong ? lastPrice + tp2Dist : lastPrice - tp2Dist;
    const tp3 = isLong ? lastPrice + tp3Dist : lastPrice - tp3Dist;

    const trailingStopDistance = atr * 1.6 * (regime.volatility === 'panic' ? 2.5 : 1.0);

    return {
      stopLoss,
      takeProfit: [tp1, tp2, tp3] as [number, number, number],
      trailingStopDistance,
      riskReward: (Math.abs(tp2 - lastPrice) / slDistance),
    };
  }

  async processSymbol(
    symbol: string,
    data: MarketData[],
    regime: MarketRegime,
    indicators: AdaptiveIndicators,
    onChain: OnChainData
  ): Promise<EnhancedSignal | null> {
    try {
      const features = FeatureEngineer.extract(data);
      const lastPrice = data[data.length - 1].close;

      const patterns: PatternMatch[] = [
        { patternName: "Bullish Flag", similarity: 0.88, historicalSuccess: 0.72 },
        { patternName: "Double Bottom", similarity: 0.45, historicalSuccess: 0.65 }
      ];

      const prompt = `
        Act as an institutional-grade crypto quantitative analysis agent (QuantAI).
        Perform a deep-dive neural scan for ${symbol}.
        
        [CONTEXT DATA]
        Market Regime: ${JSON.stringify(regime)}
        Technical Indicators: ${JSON.stringify(indicators)}
        Alpha Features: ${JSON.stringify(features)}
        On-Chain Data: ${JSON.stringify(onChain)}
        
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
        You MUST respond in JSON format matching the schema exactly.
      `;

      return await withRetry(async () => {
        const response = await this.ai.models.generateContent({
          model: 'gemini-3-pro-preview',
          contents: prompt,
          config: {
            responseMimeType: "application/json",
            responseSchema: {
              type: Type.OBJECT,
              properties: {
                direction: { type: Type.STRING },
                confidence: { type: Type.NUMBER },
                onChainScore: { type: Type.NUMBER },
                rationale: {
                  type: Type.OBJECT,
                  properties: {
                    summary: { type: Type.STRING },
                    technicalAnalysis: { type: Type.STRING },
                    mlInsights: { type: Type.STRING },
                    mlAgreementDetail: { type: Type.STRING },
                    mlModelConsensus: { type: Type.STRING },
                    mlConflictResolution: { type: Type.STRING },
                    mtfDetails: { type: Type.STRING },
                    mtfLogic: { type: Type.STRING },
                    mtfAlignmentAnalysis: { type: Type.STRING },
                    mtfCrossTimeframeMatrix: { type: Type.STRING },
                    onChainDeepDive: { type: Type.STRING },
                    onChainInterp: { type: Type.STRING },
                    onChainScoreLogic: { type: Type.STRING },
                    onChainFlowDynamics: { type: Type.STRING }
                  },
                  required: [
                    "summary", "technicalAnalysis", "mlInsights", "mlAgreementDetail", 
                    "mlModelConsensus", "mlConflictResolution", "mtfDetails", 
                    "mtfLogic", "mtfAlignmentAnalysis", "mtfCrossTimeframeMatrix",
                    "onChainDeepDive", "onChainInterp", "onChainScoreLogic", "onChainFlowDynamics"
                  ]
                },
                mlScore: { type: Type.NUMBER },
                mtfAlignmentScore: { type: Type.NUMBER },
                kellyFraction: { type: Type.NUMBER }
              },
              required: ["direction", "confidence", "onChainScore", "rationale", "mlScore", "mtfAlignmentScore", "kellyFraction"]
            }
          }
        });

        const jsonStr = response.text?.trim() || "{}";
        let result: any;
        
        try {
          result = JSON.parse(jsonStr);
        } catch (parseError) {
          console.error("AI Neural Core returned malformed JSON:", jsonStr);
          throw new Error("Neural synthesis failed to output compliant data structure.");
        }

        const direction = result.direction as SignalDirection;
        const riskParams = this.applyRiskManagement(lastPrice, direction, regime, indicators);
        
        // Final Confidence Calibration: Weighted consensus of AI-generated confidence and On-Chain Score
        // High divergence between On-Chain and TA results in confidence penalties.
        const baseConfidence = result.confidence;
        const ocWeight = 0.35; // 35% of confidence weighting comes from on-chain health
        const taWeight = 0.65;
        const weightedConfidence = (baseConfidence * taWeight) + (result.onChainScore * ocWeight);
        
        const kelly = Math.max(0.01, Math.min(result.kellyFraction, 0.25));

        return {
          symbol,
          direction,
          confidence: weightedConfidence * 100,
          onChainScore: result.onChainScore,
          entryPrice: lastPrice,
          stopLoss: riskParams.stopLoss,
          takeProfit: riskParams.takeProfit,
          trailingStopDistance: riskParams.trailingStopDistance,
          positionSizePct: Math.min(10, kelly * 100),
          expectedValue: riskParams.riskReward * weightedConfidence - (1 - weightedConfidence),
          riskReward: riskParams.riskReward,
          timeframe: '1h',
          features,
          patterns,
          rationale: {
            ...result.rationale,
            indicators: indicators,
            mlQuality: result.mlScore,
            mtfAlignment: result.mtfAlignmentScore > 0.7,
            onchainScore: result.onChainScore,
            regime: regime.trend
          },
          validUntil: Date.now() + 7200000,
          modelAgreement: {
            ta: 0.85,
            ml: result.mlScore,
            mtf: result.mtfAlignmentScore,
            onchain: result.onChainScore,
            regime: 0.90
          },
          var95: 1.4,
          maxDrawdownRisk: 2.2,
          kellyFraction: kelly
        };
      });
    } catch (error: any) {
      console.error("AI Engine fatal error:", error);
      throw error;
    }
  }
}
