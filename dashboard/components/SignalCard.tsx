import React from 'react';
import { MarketSignal, SignalType } from '../types';

interface SignalCardProps {
  signal: MarketSignal;
  onClick: (signal: MarketSignal) => void;
}

const SignalCard: React.FC<SignalCardProps> = ({ signal, onClick }) => {
  const isBuy = signal.type.includes('BUY');
  const isSell = signal.type.includes('SELL');

  return (
    <div 
      onClick={() => onClick(signal)}
      className="bg-white rounded-3xl p-5 shadow-sm border border-gray-100 active:scale-[0.98] transition-all cursor-pointer mb-3"
    >
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="text-lg font-black text-slate-800 tracking-tight">{signal.asset}</h3>
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            {new Date(signal.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {signal.timeframe}
          </p>
        </div>
        <div className={`px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest ${
          isBuy ? 'bg-emerald-100 text-emerald-600' : 
          isSell ? 'bg-rose-100 text-rose-600' : 
          'bg-gray-100 text-gray-600'
        }`}>
          {signal.type}
        </div>
      </div>

      <div className="flex justify-between items-end mt-4">
        <div>
          <div className="text-xl font-black text-slate-900 mono tracking-tighter">${signal.price.toLocaleString(undefined, { maximumFractionDigits: 4 })}</div>
          <div className={`text-[10px] font-black tracking-widest uppercase ${signal.change24h >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
            {signal.change24h >= 0 ? '▲' : '▼'} {Math.abs(signal.change24h).toFixed(2)}%
          </div>
        </div>
        
        <div className="flex flex-col items-end gap-1.5">
          <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Confidence</span>
          <div className="w-20 h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all duration-700 ${isBuy ? 'bg-emerald-500' : isSell ? 'bg-rose-500' : 'bg-blue-500'}`}
              style={{ width: `${signal.strength}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignalCard;