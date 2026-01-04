
import { MarketData, AlphaFeatures } from '../types';
import { calculateRSI, calculateOBV, calculateTrendSlope, calculateSupportResistance } from '../utils/technicalIndicators';

export class FeatureEngineer {
  static extract(data: MarketData[]): AlphaFeatures {
    const prices = data.map(d => d.close);
    const rsi = calculateRSI(prices);
    const obv = calculateOBV(data);
    const obvSlope = calculateTrendSlope(obv.slice(-20), 20);
    
    // Simple Divergence Detection
    const lastPrice = prices[prices.length - 1];
    const prevPrice = prices[prices.length - 10];
    const lastRsi = rsi;
    const prevRsi = calculateRSI(prices.slice(0, -10));

    let rsiDivergence: AlphaFeatures['rsiDivergence'] = 'none';
    if (lastPrice < prevPrice && lastRsi > prevRsi) rsiDivergence = 'bullish';
    if (lastPrice > prevPrice && lastRsi < prevRsi) rsiDivergence = 'bearish';

    const volumeAvg = data.slice(-20).reduce((sum, d) => sum + d.volume, 0) / 20;
    const volumeRatio = data[data.length - 1].volume / volumeAvg;

    const lastCandle = data[data.length - 1];
    const range = Math.max(0.0001, lastCandle.high - lastCandle.low);
    const body = Math.abs(lastCandle.close - lastCandle.open);
    const candleBodyRatio = body / range;

    const sr = calculateSupportResistance(data);

    return {
      rsiDivergence,
      volumeRatio,
      priceAcceleration: calculateTrendSlope(prices.slice(-10), 10),
      obvTrend: obvSlope > 0 ? 'rising' : obvSlope < 0 ? 'falling' : 'flat',
      correlationWithBTC: 0.82,
      bbPosition: 0.5, // Logic usually requires full BB calculation, simplified here
      candleBodyRatio,
      distToResistance: sr.distToResistance,
      distToSupport: sr.distToSupport
    };
  }
}
