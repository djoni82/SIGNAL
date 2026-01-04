import React from 'react';
import { PortfolioState } from '../types';

interface Props {
  data: PortfolioState;
}

const PortfolioCard: React.FC<Props> = ({ data }) => {
  return (
    <div className="bg-gradient-to-br from-indigo-600 to-indigo-800 rounded-[2rem] p-6 text-white shadow-xl shadow-indigo-200">
      <div className="flex justify-between items-start mb-6">
        <div>
          <p className="text-xs font-bold text-indigo-200 uppercase tracking-widest mb-1">Total Assets</p>
          <h2 className="text-3xl font-black tracking-tight">${data.totalValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}</h2>
        </div>
        <div className="bg-white/20 p-2 rounded-xl backdrop-blur-md">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
      </div>
      
      <div className="flex gap-6">
        <div>
          <p className="text-[10px] font-bold text-indigo-200 uppercase tracking-tighter">Profit 24h</p>
          <p className="text-sm font-bold">+${data.dailyPnL.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-[10px] font-bold text-indigo-200 uppercase tracking-tighter">Change</p>
          <p className="text-sm font-bold">+{data.dailyChangePercent.toFixed(2)}%</p>
        </div>
      </div>
    </div>
  );
};

export default PortfolioCard;