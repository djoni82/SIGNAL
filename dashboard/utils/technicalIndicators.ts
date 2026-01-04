
import { MarketData, MarketPhase } from '../types';

export const calculateSMA = (data: number[], period: number): number => {
  if (data.length < period) return 0;
  return data.slice(-period).reduce((a, b) => a + b, 0) / period;
};

export const calculateEMA = (data: number[], period: number): number => {
  if (data.length < period) return 0;
  const k = 2 / (period + 1);
  let ema = calculateSMA(data.slice(0, period), period);
  for (let i = period; i < data.length; i++) {
    ema = data[i] * k + ema * (1 - k);
  }
  return ema;
};

export const calculateRSI = (data: number[], period: number = 14): number => {
  if (data.length <= period) return 50;
  let gains = 0;
  let losses = 0;

  for (let i = data.length - period; i < data.length; i++) {
    const diff = data[i] - data[i - 1];
    if (diff >= 0) gains += diff;
    else losses -= diff;
  }

  if (losses === 0) return 100;
  const rs = (gains / period) / (losses / period);
  return 100 - (100 / (1 + rs));
};

export const calculateATR = (data: MarketData[], period: number = 14): number => {
  if (data.length <= period) return 0;
  const trs: number[] = [];
  for (let i = 1; i < data.length; i++) {
    const h = data[i].high;
    const l = data[i].low;
    const pc = data[i - 1].close;
    trs.push(Math.max(h - l, Math.abs(h - pc), Math.abs(l - pc)));
  }
  return calculateSMA(trs, period);
};

export const calculateADX = (data: MarketData[], period: number = 14): number => {
  if (data.length < period * 2) return 20;
  const tr = calculateATR(data, period);
  const upMoves: number[] = [];
  const downMoves: number[] = [];
  
  for (let i = 1; i < data.length; i++) {
    const dmPlus = data[i].high - data[i-1].high;
    const dmMinus = data[i-1].low - data[i].low;
    upMoves.push(dmPlus > dmMinus && dmPlus > 0 ? dmPlus : 0);
    downMoves.push(dmMinus > dmPlus && dmMinus > 0 ? dmMinus : 0);
  }
  
  const smoothedPlus = calculateSMA(upMoves, period);
  const smoothedMinus = calculateSMA(downMoves, period);
  const diPlus = (smoothedPlus / tr) * 100;
  const diMinus = (smoothedMinus / tr) * 100;
  const dx = (Math.abs(diPlus - diMinus) / (diPlus + diMinus)) * 100;
  return dx || 20;
};

export const calculateTrendSlope = (data: number[], period: number = 20): number => {
  if (data.length < period) return 0;
  const slice = data.slice(-period);
  const xMean = (period - 1) / 2;
  const yMean = slice.reduce((a, b) => a + b, 0) / period;
  let num = 0;
  let den = 0;
  for (let i = 0; i < period; i++) {
    num += (i - xMean) * (slice[i] - yMean);
    den += (i - xMean) ** 2;
  }
  return num / den;
};

export const calculateOBV = (data: MarketData[]): number[] => {
  const obv = [0];
  for (let i = 1; i < data.length; i++) {
    let currentOBV = obv[i - 1];
    if (data[i].close > data[i - 1].close) {
      currentOBV += data[i].volume;
    } else if (data[i].close < data[i - 1].close) {
      currentOBV -= data[i].volume;
    }
    obv.push(currentOBV);
  }
  return obv;
};

export const calculateSupportResistance = (data: MarketData[]) => {
  const highs = data.map(d => d.high);
  const lows = data.map(d => d.low);
  const lastPrice = data[data.length - 1].close;

  // Simple peak/trough detection
  const resistance = Math.max(...highs.slice(-20));
  const support = Math.min(...lows.slice(-20));

  return {
    support,
    resistance,
    distToSupport: (lastPrice - support) / lastPrice,
    distToResistance: (resistance - lastPrice) / lastPrice
  };
};

export const detectWyckoffPhase = (data: MarketData[]): MarketPhase => {
  const rsi = calculateRSI(data.map(d => d.close));
  const slope = calculateTrendSlope(data.map(d => d.close));
  if (rsi < 35 && slope > -0.1) return 'accumulation';
  if (slope > 0.5) return 'markup';
  if (rsi > 65 && slope < 0.1) return 'distribution';
  if (slope < -0.5) return 'markdown';
  return 'neutral';
};
