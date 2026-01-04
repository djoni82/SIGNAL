import { GoogleGenAI, Type } from "@google/genai";
import { MarketSignal, AnalysisResponse, OnChainData } from "../types";
import { withRetry } from "../utils/apiUtils";

/**
 * Institutional AI analysis using Gemini 3.
 */
export const analyzeSignal = async (signal: MarketSignal, onChain: OnChainData): Promise<AnalysisResponse> => {
  // Initialize GoogleGenAI client with required API key configuration.
  const apiKey = (process.env as any).API_KEY;
  const ai = new GoogleGenAI({ apiKey: apiKey || "" });

  const prompt = `Act as an institutional crypto quantitative trader. 
    Analyze this ${signal.asset} signal setup combining Market Data and On-Chain Metrics:
    
    [MARKET CONTEXT]
    Current Price: ${signal.price}
    Regime: ${signal.regime}
    Volatility: ${signal.volatility}
    Technical Context: RSI(${signal.indicators.rsi}), MACD(${signal.indicators.macd}), ADX(${signal.indicators.adx.toFixed(1)})
    
    [ON-CHAIN METRICS]
    Exchange Net Flow: ${onChain.exchangeNetFlow} (Positive=Inflow, Negative=Outflow)
    Active Addresses: ${onChain.activeAddresses}
    MVRV Ratio: ${onChain.mvrvRatio.toFixed(2)}
    Whale Transaction Count (24h): ${onChain.whaleTransactionCount}
    
    [RISK PARAMETERS]
    Entry: ${signal.risk.entry}
    Stop Loss: ${signal.risk.stopLoss}
    Take Profits: ${signal.risk.takeProfit.join(', ')}
    
    Predict the next significant move and provide a detailed logic. 
    Critically interpret the On-Chain data: Do flows suggest accumulation or distribution? Is the MVRV suggesting overvaluation? 
    Calculate a final On-Chain Score (0-1) and expected move.`;

  return withRetry(async () => {
    try {
      const response = await ai.models.generateContent({
        model: "gemini-3-flash-preview",
        contents: prompt,
        config: {
          responseMimeType: "application/json",
          responseSchema: {
            type: Type.OBJECT,
            properties: {
              sentiment: {
                type: Type.STRING,
                description: "Primary market sentiment: Bullish, Bearish, or Neutral."
              },
              reasoning: {
                type: Type.STRING,
                description: "Detailed institutional logic for the prediction, including on-chain interpretation."
              },
              riskLevel: {
                type: Type.STRING,
                description: "Assessment: LOW, MEDIUM, or HIGH."
              },
              confidence: {
                type: Type.NUMBER,
                description: "Confidence level between 0 and 1."
              },
              onChainScore: {
                type: Type.NUMBER,
                description: "On-chain health score between 0 and 1."
              },
              expectedMove: {
                type: Type.STRING,
                description: "Targeted price movement or percentage."
              }
            },
            required: ["sentiment", "reasoning", "riskLevel", "confidence", "onChainScore", "expectedMove"]
          }
        }
      });

      const jsonStr = response.text?.trim() || "{}";
      return JSON.parse(jsonStr);
    } catch (error) {
      console.error("AI Engine Internal Error:", error);
      throw error;
    }
  });
};
