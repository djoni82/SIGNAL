
import React, { useMemo } from 'react';
import { MarketData, MarketRegime, AdaptiveIndicators } from '../types';
import { calculateRSI, calculateEMA, calculateADX, calculateATR } from '../utils/technicalIndicators';
import { BarChart3 } from 'lucide-react';

interface Props {
  data: MarketData[];
  regime: MarketRegime;
  onIndicatorsCalculated: (indicators: AdaptiveIndicators) => void;
}

const AdaptiveIndicatorEngine: React.FC<Props> = ({ data, regime, onIndicatorsCalculated }) => {
  const indicators = useMemo(() => {
    const prices = data.map(d => d.close);
    const rsiVal = calculateRSI(prices);
    const emaShort = calculateEMA(prices, 12);
    const emaLong = calculateEMA(prices, 26);
    const adx = calculateADX(data);
    const atr = calculateATR(data);

    const result: AdaptiveIndicators = {
      rsi: { value: rsiVal, period: 14 },
      bollinger: { upper: 0, middle: 0, lower: 0, width: 0 },
      ema: { short: emaShort, long: emaLong },
      macd: { value: emaShort - emaLong, signal: 0, histogram: 0 },
      adx,
      atr,
      timestamp: Date.now()
    };

    onIndicatorsCalculated(result);
    return result;
  }, [data, regime]);

  return (
    <div className="p-6 bg-[#0d1117]">
      <div className="flex items-center gap-2 mb-6">
        <BarChart3 className="w-5 h-5 text-emerald-500" />
        <h3 className="font-black text-slate-100 uppercase tracking-tighter">Adaptive Core</h3>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="text-center">
          <div className="text-[10px] text-slate-500 font-bold uppercase mb-2">RSI</div>
          <div className={`text-3xl font-black ${indicators.rsi.value < 30 ? 'text-emerald-400' : indicators.rsi.value > 70 ? 'text-rose-400' : 'text-slate-100'}`}>
            {indicators.rsi.value.toFixed(1)}
          </div>
          <div className="mt-3 w-full h-1 bg-slate-800 rounded-full overflow-hidden relative">
             <div className="absolute top-0 h-full bg-indigo-500" style={{ left: `${indicators.rsi.value}%`, width: '4px', marginLeft: '-2px' }}></div>
          </div>
        </div>

        <div className="text-center">
          <div className="text-[10px] text-slate-500 font-bold uppercase mb-2">MACD Diff</div>
          <div className={`text-3xl font-black ${indicators.macd.value > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {indicators.macd.value.toFixed(2)}
          </div>
          <div className="text-[10px] text-slate-600 font-bold mt-1 uppercase">Momentum</div>
        </div>

        <div className="text-center">
          <div className="text-[10px] text-slate-500 font-bold uppercase mb-2">Range</div>
          <div className="text-3xl font-black text-slate-100 mono">
            ${indicators.atr.toFixed(2)}
          </div>
          <div className="text-[10px] text-slate-600 font-bold mt-1 uppercase">ATR (14)</div>
        </div>
      </div>
    </div>
  );
};

export default AdaptiveIndicatorEngine;
