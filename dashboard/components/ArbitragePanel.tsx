import React from 'react';
import { ArbitrageOpportunity } from '../types';
import { ArrowRight, Layers, Repeat, Zap, AlertCircle } from 'lucide-react';

interface Props {
  opportunities: ArbitrageOpportunity[];
  onExecute: (opp: ArbitrageOpportunity) => void;
}

const ArbitragePanel: React.FC<Props> = ({ opportunities, onExecute }) => {
  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-500">
      <div className="flex justify-between items-center mb-6 px-1">
        <h2 className="text-lg font-black tracking-tight text-slate-900">Arbitrage Scan</h2>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse"></span>
          <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Multi-Venue Monitoring</span>
        </div>
      </div>

      {opportunities.length === 0 ? (
        <div className="py-24 text-center bg-white rounded-[2.5rem] border border-dashed border-gray-200">
          <Layers className="w-12 h-12 text-slate-200 mx-auto mb-4" />
          <p className="text-[10px] font-black text-slate-300 uppercase tracking-widest">Scanning Liquidity Pools...</p>
        </div>
      ) : (
        opportunities.map((opp) => (
          <div 
            key={opp.id}
            className="group bg-white rounded-3xl p-6 border border-gray-100 shadow-sm hover:shadow-md transition-all active:scale-[0.98]"
          >
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${opp.type === 'Triangular' ? 'bg-indigo-50 text-indigo-600' : 'bg-cyan-50 text-cyan-600'}`}>
                  {opp.type === 'Triangular' ? <Repeat size={20} /> : <Layers size={20} />}
                </div>
                <div>
                  <h3 className="text-base font-black text-slate-900 tracking-tight">{opp.asset}</h3>
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{opp.type}</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xl font-black text-emerald-500 mono">+{opp.profitPct.toFixed(2)}%</div>
                <div className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Est. Net Profit</div>
              </div>
            </div>

            <div className="bg-slate-50 rounded-2xl p-4 flex items-center justify-between mb-4 border border-gray-100/50">
              <div className="flex items-center gap-2">
                {opp.path ? (
                  <div className="flex items-center gap-1.5">
                    {opp.path.map((step, i) => (
                      <React.Fragment key={step}>
                        <span className="text-[10px] font-black text-slate-600">{step}</span>
                        {i < opp.path!.length - 1 && <ArrowRight size={10} className="text-slate-300" />}
                      </React.Fragment>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-black text-slate-600 uppercase">{opp.venues[0]}</span>
                    <ArrowRight size={10} className="text-slate-300" />
                    <span className="text-[10px] font-black text-slate-600 uppercase">{opp.venues[1]}</span>
                  </div>
                )}
              </div>
              <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest ${
                opp.executionRisk === 'Low' ? 'bg-emerald-50 text-emerald-600' : 
                opp.executionRisk === 'Medium' ? 'bg-amber-50 text-amber-600' : 'bg-rose-50 text-rose-600'
              }`}>
                {opp.executionRisk === 'High' && <AlertCircle size={10} />}
                {opp.executionRisk} Risk
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div>
                  <p className="text-[8px] font-black text-slate-400 uppercase tracking-widest mb-0.5">Spread</p>
                  <p className="text-xs font-black text-slate-700 mono">${opp.spread.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-[8px] font-black text-slate-400 uppercase tracking-widest mb-0.5">Venues</p>
                  <p className="text-xs font-black text-slate-700">{opp.venues.join(', ')}</p>
                </div>
              </div>
              <button 
                onClick={() => onExecute(opp)}
                className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-slate-800 transition-colors shadow-lg shadow-slate-900/10"
              >
                Execute <Zap size={12} fill="currentColor" />
              </button>
            </div>
          </div>
        ))
      )}
    </div>
  );
};

export default ArbitragePanel;
