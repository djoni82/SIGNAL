
import React, { useEffect, useState } from 'react';
import { MarketRegime, MarketData } from '../types';
import { calculateADX, calculateATR, calculateTrendSlope, detectWyckoffPhase } from '../utils/technicalIndicators';
import { Activity, ShieldAlert, Zap, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MarketRegimeDetectorProps {
  data: MarketData[];
  symbol: string;
  onRegimeDetected: (regime: MarketRegime) => void;
}

const MarketRegimeDetector: React.FC<MarketRegimeDetectorProps> = ({
  data,
  symbol,
  onRegimeDetected
}) => {
  const [regime, setRegime] = useState<MarketRegime | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const detect = async () => {
      if (data.length < 50) return;
      setLoading(true);
      try {
        const adx = calculateADX(data);
        const slope = calculateTrendSlope(data.map(d => d.close));
        const atr = calculateATR(data);
        const lastPrice = data[data.length - 1].close;
        const atrPct = (atr / lastPrice) * 100;
        
        let trend: MarketRegime['trend'] = 'neutral';
        if (adx > 25) trend = slope > 0 ? 'bullish' : 'bearish';
        
        let volatility: MarketRegime['volatility'] = 'medium';
        if (atrPct > 5) volatility = 'panic';
        else if (atrPct > 3) volatility = 'high';
        else if (atrPct < 1.5) volatility = 'low';
        
        const phase = detectWyckoffPhase(data);
        const newRegime: MarketRegime = { trend, strength: adx, volatility, volatilityValue: atrPct, btcCorrelation: 0.85, phase, crisisMode: volatility === 'panic' };
        
        setRegime(newRegime);
        onRegimeDetected(newRegime);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    detect();
  }, [data, symbol]);

  if (loading) return <div className="p-6 bg-[#0d1117] animate-pulse h-48 rounded-3xl" />;
  if (!regime) return null;

  return (
    <div className="p-6 bg-[#0d1117]">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-indigo-500" />
          <h3 className="font-black text-slate-100 uppercase tracking-tighter">Market Regime</h3>
        </div>
        <div className={`px-2 py-0.5 rounded text-[10px] font-black border ${regime.crisisMode ? 'bg-rose-500/20 text-rose-500 border-rose-500/50' : 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'}`}>
          {regime.crisisMode ? 'CRISIS MODE' : 'STABLE'}
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-[#161b22] rounded-2xl border border-slate-800">
          <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Direction</span>
          <div className="flex items-center gap-2">
            {regime.trend === 'bullish' ? <TrendingUp className="w-4 h-4 text-emerald-400" /> : 
             regime.trend === 'bearish' ? <TrendingDown className="w-4 h-4 text-rose-400" /> : 
             <Minus className="w-4 h-4 text-slate-500" />}
            <span className={`text-sm font-black ${regime.trend === 'bullish' ? 'text-emerald-400' : regime.trend === 'bearish' ? 'text-rose-400' : 'text-slate-400'}`}>
              {regime.trend.toUpperCase()}
            </span>
          </div>
        </div>

        <div className="p-4 bg-[#161b22] rounded-2xl border border-slate-800">
          <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Volatility</span>
          <div className="flex items-center gap-2">
            {regime.volatility === 'panic' && <ShieldAlert className="w-4 h-4 text-rose-500" />}
            <span className={`text-sm font-black ${regime.volatility === 'panic' ? 'text-rose-400' : regime.volatility === 'high' ? 'text-amber-400' : 'text-indigo-400'}`}>
              {regime.volatility.toUpperCase()}
            </span>
          </div>
        </div>

        <div className="p-4 bg-[#161b22] rounded-2xl border border-slate-800">
          <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Phase</span>
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-400" />
            <span className="text-sm font-black text-slate-100 capitalize">{regime.phase}</span>
          </div>
        </div>

        <div className="p-4 bg-[#161b22] rounded-2xl border border-slate-800">
          <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Strength (ADX)</span>
          <div className="flex items-center justify-between">
            <span className="text-sm font-black text-slate-100">{regime.strength.toFixed(0)}</span>
            <div className="w-16 h-1 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.5)]" style={{ width: `${Math.min(100, regime.strength)}%` }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketRegimeDetector;
