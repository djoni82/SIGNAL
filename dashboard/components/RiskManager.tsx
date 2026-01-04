
import React from 'react';
import { EnhancedSignal, MarketRegime } from '../types';
import { ShieldCheck, Target, TrendingUp, Anchor, Zap, ShieldOff, Activity, AlertTriangle, ArrowRight, Info, Crosshair, MoveDiagonal } from 'lucide-react';

interface Props {
  signal: EnhancedSignal;
  regime: MarketRegime;
  totalCapital: number;
}

const RiskManager: React.FC<Props> = ({ signal, regime, totalCapital }) => {
  const riskAmount = (totalCapital * signal.positionSizePct) / 100;

  const volColors = {
    low: 'text-indigo-400',
    medium: 'text-emerald-400',
    high: 'text-amber-400',
    panic: 'text-rose-400'
  };

  const adx = regime.strength;
  const isHighStrength = adx > 25;

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-indigo-500" />
          <h3 className="font-black text-white uppercase tracking-tighter text-sm">Neural Risk Guard v9.2</h3>
        </div>
        <div className="flex items-center gap-1.5 bg-indigo-500/10 px-2.5 py-1 rounded-full border border-indigo-500/20">
          <Zap size={10} className="text-amber-400" />
          <span className="text-[9px] font-black text-amber-400 uppercase tracking-widest">
            {regime.phase.toUpperCase()} TUNED
          </span>
        </div>
      </div>

      {/* Logic Dashboard */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-4 bg-[#161b22] rounded-2xl border border-slate-800 flex flex-col justify-between group transition-all hover:border-indigo-500/30">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Activity size={12} className="text-indigo-400" />
              <span className="text-[9px] font-black text-slate-500 uppercase tracking-wider">Momentum Scaling</span>
            </div>
            <p className={`text-xs font-black uppercase ${isHighStrength ? 'text-emerald-400' : 'text-slate-400'}`}>
              {isHighStrength ? 'Aggressive Tightening' : 'Wide Volatility Buffer'}
            </p>
          </div>
          <div className="mt-3">
            <div className="flex justify-between text-[8px] text-slate-600 font-bold mb-1 uppercase">
              <span>ADX: {adx.toFixed(0)}</span>
              <span>Bias: {isHighStrength ? 'TIGHT' : 'WIDE'}</span>
            </div>
            <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.5)]" style={{ width: `${Math.min(100, adx * 2.5)}%` }}></div>
            </div>
          </div>
        </div>

        <div className="p-4 bg-[#161b22] rounded-2xl border border-slate-800 flex flex-col justify-between group transition-all hover:border-rose-500/30">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <MoveDiagonal size={12} className="text-rose-400" />
              <span className="text-[9px] font-black text-slate-500 uppercase tracking-wider">Volatility Offset</span>
            </div>
            <p className={`text-xs font-black uppercase ${volColors[regime.volatility]}`}>
              {regime.volatility.toUpperCase()} Risk Band
            </p>
          </div>
          <p className="text-[9px] font-bold text-slate-500 leading-tight mt-2 italic">
            {regime.crisisMode ? 'Crisis Multiplier: 1.4x' : 'Stability Multiplier: 1.0x'}
          </p>
        </div>
      </div>

      {/* Primary Parameters */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-[#1c2128] rounded-2xl border border-slate-800 shadow-inner">
          <div className="flex items-center gap-2 mb-2">
            <Crosshair size={14} className="text-indigo-400" />
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Max Risk Amount</span>
          </div>
          <p className="text-xl font-black text-white mono tracking-tighter">${riskAmount.toFixed(2)}</p>
          <p className="text-[9px] font-black text-slate-600 uppercase mt-1 tracking-wider">{signal.positionSizePct.toFixed(1)}% Portfolio</p>
        </div>
        <div className="p-4 bg-[#1c2128] rounded-2xl border border-slate-800 shadow-inner">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp size={14} className="text-emerald-400" />
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Signal Efficiency</span>
          </div>
          <p className="text-xl font-black text-emerald-400 mono tracking-tighter">1:{signal.riskReward.toFixed(2)}</p>
          <p className="text-[9px] font-black text-slate-600 uppercase mt-1 tracking-wider">Net R:R Ratio</p>
        </div>
      </div>

      {/* Stop & Trailing Visualization */}
      <div className="relative p-6 bg-[#0d1117] border border-slate-800 rounded-[2.5rem] overflow-hidden group shadow-2xl">
        <div className="absolute top-0 left-0 w-2 h-full bg-rose-500/80 shadow-[0_0_20px_rgba(244,63,94,0.4)]"></div>
        <div className="flex justify-between items-start mb-6">
          <div>
            <span className="text-[10px] font-black text-rose-400 uppercase tracking-[0.2em] block mb-1">Adaptive Hard Stop</span>
            <p className="text-3xl font-black text-white mono tracking-tighter">
              ${signal.stopLoss.toLocaleString(undefined, { maximumFractionDigits: 4 })}
            </p>
          </div>
          <div className="text-right">
            <span className="text-[10px] font-black text-slate-500 uppercase tracking-wider block mb-2">TSL Protocol</span>
            <div className="inline-flex items-center gap-2 bg-indigo-500/10 px-3 py-1.5 rounded-xl border border-indigo-500/30">
              <ShieldOff size={12} className="text-indigo-400" />
              <span className="text-[10px] font-black text-indigo-400 mono">
                ±${signal.trailingStopDistance.toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-[#161b22] p-4 rounded-2xl border border-slate-800/50">
          <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-3">
            <Info size={12} className="text-slate-600" />
            <span>Institutional Logic Chain</span>
          </div>
          <div className="flex items-center justify-between text-xs font-black text-slate-300 mono bg-black/30 p-3 rounded-xl border border-white/5">
            <div className="text-center">
              <p className="text-[8px] text-slate-600 uppercase mb-1">Vol</p>
              <span className="text-indigo-400">{regime.volatilityValue.toFixed(1)}%</span>
            </div>
            <ArrowRight size={12} className="text-slate-700" />
            <div className="text-center">
              <p className="text-[8px] text-slate-600 uppercase mb-1">ADX-B</p>
              <span className="text-amber-400">{adx.toFixed(0)}</span>
            </div>
            <ArrowRight size={12} className="text-slate-700" />
            <div className="text-center">
              <p className="text-[8px] text-slate-600 uppercase mb-1">Multiplier</p>
              <span className="text-emerald-400">×{((signal.entryPrice - signal.stopLoss) / signal.rationale.indicators.atr).toFixed(1)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* TP Targets Ladder */}
      <div className="p-8 bg-[#1c2128] border border-slate-800 rounded-[3rem] shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 p-6 opacity-[0.03]">
          <TrendingUp size={120} />
        </div>
        <div className="flex items-center gap-3 mb-8 relative z-10">
          <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 flex items-center justify-center">
            <TrendingUp size={20} className="text-emerald-400" />
          </div>
          <p className="text-[11px] font-black text-slate-400 uppercase tracking-[0.4em]">Target Execution Ladder</p>
        </div>

        <div className="space-y-4 relative z-10">
          {signal.takeProfit.map((tp, idx) => (
            <div key={idx} className="group transition-all transform hover:translate-x-1">
              <div className={`flex justify-between items-center p-5 rounded-[1.75rem] border ${idx === 0 ? 'bg-indigo-500/5 border-indigo-500/20' :
                  idx === 1 ? 'bg-emerald-500/5 border-emerald-500/10' :
                    'bg-emerald-500/10 border-emerald-500/30 shadow-[0_0_30px_rgba(16,185,129,0.08)]'
                }`}>
                <div className="flex items-center gap-5">
                  <div className={`w-11 h-11 rounded-2xl flex items-center justify-center font-black text-sm shadow-xl ${idx === 0 ? 'bg-indigo-600 text-white shadow-indigo-500/20' : 'bg-slate-800 text-emerald-400 border border-emerald-500/20'
                    }`}>
                    {idx === 0 ? <Anchor size={20} /> : idx + 1}
                  </div>
                  <div>
                    <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest block mb-1">
                      {idx === 0 ? 'Protocol Breakeven' : idx === 1 ? 'Alpha Extraction' : 'Momentum Extension'}
                    </span>
                    <span className="text-xl font-black text-white mono tracking-tighter">
                      ${tp.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`text-[10px] font-black tracking-[0.2em] px-3 py-1.5 rounded-xl ${idx === 0 ? 'text-indigo-400 bg-indigo-400/10' : 'text-emerald-400 bg-emerald-400/10'
                    }`}>
                    {idx === 0 ? '1.5R' : idx === 1 ? '3.0R' : '6.0R'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Logic Alert */}
      <div className="flex items-start gap-4 p-5 bg-amber-500/5 border border-amber-500/10 rounded-[2rem]">
        <AlertTriangle size={20} className="text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="text-[11px] font-black text-white uppercase tracking-wider">Neural Risk Context</p>
          <p className="text-[10px] text-slate-400 font-medium leading-relaxed">
            Stop loss is dynamically offset at <span className="text-white font-bold">{((signal.entryPrice - signal.stopLoss) / signal.rationale.indicators.atr).toFixed(1)}× ATR</span>.
            This ensures protection against <span className="text-white font-bold">{regime.volatility} volatility</span> spikes while the <span className="text-white font-bold">trailing stop</span> protocol captures parabolic trend expansion.
          </p>
        </div>
      </div>
    </div>
  );
};

export default RiskManager;
