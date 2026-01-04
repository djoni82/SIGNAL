
export enum SignalType {
  STRONG_BUY = 'STRONG BUY',
  BUY = 'BUY',
  NEUTRAL = 'NEUTRAL',
  SELL = 'SELL',
  STRONG_SELL = 'STRONG SELL'
}

export enum MarketRegimeType {
  BULLISH_TREND = 'Bullish Trend',
  BEARISH_TREND = 'Bearish Trend',
  ACCUMULATION = 'Accumulation',
  DISTRIBUTION = 'Distribution',
  HIGH_VOLATILITY = 'High Volatility'
}

export interface MarketRegime {
  trend: 'bullish' | 'bearish' | 'neutral';
  strength: number;
  volatility: 'low' | 'medium' | 'high' | 'panic';
  volatilityValue: number;
  btcCorrelation: number;
  phase: MarketPhase;
  crisisMode: boolean;
}

export enum VolatilityLevel {
  LOW = 'Low',
  MEDIUM = 'Medium',
  HIGH = 'High',
  EXTREME = 'Extreme'
}

export interface MarketData {
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  timestamp: number;
}

export type MarketPhase = 'accumulation' | 'markup' | 'distribution' | 'markdown' | 'neutral';

export interface AdaptiveIndicators {
  rsi: { value: number; period: number };
  bollinger: { upper: number; middle: number; lower: number; width: number };
  ema: { short: number; long: number };
  macd: { value: number; signal: number; histogram: number };
  adx: number;
  atr: number;
  timestamp: number;
}

export type SignalDirection = 'STRONG_BUY' | 'BUY' | 'NEUTRAL' | 'SELL' | 'STRONG_SELL';

export interface AlphaFeatures {
  rsiDivergence: 'bullish' | 'bearish' | 'none';
  volumeRatio: number;
  priceAcceleration: number;
  obvTrend: 'rising' | 'falling' | 'flat';
  correlationWithBTC: number;
  bbPosition: number;
  candleBodyRatio: number;
  distToResistance: number;
  distToSupport: number;
}

export interface PatternMatch {
  patternName: string;
  similarity: number;
  historicalSuccess: number;
}

export interface OnChainData {
  exchangeNetFlow: number;
  activeAddresses: number;
  mvrvRatio: number;
  whaleTransactionCount: number;
  timestamp: number;
}

export interface EnhancedSignal {
  symbol: string;
  direction: SignalDirection;
  confidence: number;
  onChainScore: number;
  entryPrice: number;
  stopLoss: number;
  takeProfit: [number, number, number];
  trailingStopDistance: number;
  positionSizePct: number;
  expectedValue: number;
  riskReward: number;
  timeframe: string;
  features: AlphaFeatures;
  patterns: PatternMatch[];
  rationale: {
    summary: string;
    technicalAnalysis: string;
    mlInsights: string;
    mlAgreementDetail: string;
    mlModelConsensus: string;
    mlConflictResolution: string; // How mixed signals were reconciled
    mtfDetails: string;
    mtfLogic: string;
    mtfAlignmentAnalysis: string;
    mtfCrossTimeframeMatrix: string; // Specific detail on 15m vs 1h vs 4h
    onChainDeepDive: string;
    onChainInterp: string;
    onChainScoreLogic: string;
    onChainFlowDynamics: string; // Detailed interpretation of exchange flows
    indicators: AdaptiveIndicators;
    mlQuality: number;
    mtfAlignment: boolean;
    onchainScore: number;
    regime: string;
  };
  validUntil: number;
  modelAgreement: {
    ta: number;
    ml: number;
    mtf: number;
    onchain: number;
    regime: number;
  };
  var95: number;
  maxDrawdownRisk: number;
  kellyFraction: number;
}

export interface MarketSignal {
  id: string;
  asset: string;
  price: number;
  change24h: number;
  type: SignalType;
  strength: number;
  onChainScore: number;
  timestamp: number;
  timeframe: string;
  regime: MarketRegimeType;
  volatility: VolatilityLevel;
  indicators: {
    rsi: number;
    macd: string;
    volume: string;
    trend: string;
    adx: number;
    volumeProfile: string;
  };
  risk: {
    entry: number;
    stopLoss: number;
    takeProfit: number[];
    trailingStopDistance?: number;
    rrRatio: string;
    positionSize: number;
    expectedValue: number;
  };
}

export interface ArbitrageOpportunity {
  id: string;
  type: 'Cross-Exchange' | 'Triangular';
  asset: string;
  path?: string[];
  profitPct: number;
  expectedProfit: number;
  executionRisk: 'Low' | 'Medium' | 'High';
  venues: string[];
  spread: number;
  timestamp: number;
}

export interface AnalysisResponse {
  sentiment: string;
  reasoning: string;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  confidence: number;
  onChainScore: number;
  expectedMove: string;
}

export interface ChartDataPoint {
  time: string;
  price: number;
}

export interface PortfolioPosition {
  asset: string;
  amount: number;
  entryPrice: number;
  currentPrice: number;
}

export interface PortfolioState {
  totalValue: number;
  dailyPnL: number;
  dailyChangePercent: number;
  positions: PortfolioPosition[];
}
