import React from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { ChartDataPoint } from '../types';

interface MarketChartProps {
  data: ChartDataPoint[];
}

const MarketChart: React.FC<MarketChartProps> = ({ data }) => {
  return (
    <div className="h-48 w-full mt-2">
      {data.length === 0 ? (
        <div className="h-full w-full flex items-center justify-center bg-gray-50 rounded-2xl border border-dashed border-gray-200 text-slate-400 text-sm font-medium">
          Loading market pulse...
        </div>
      ) : (
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <XAxis dataKey="time" hide />
            <YAxis hide domain={['auto', 'auto']} />
            <Tooltip 
              contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
              labelStyle={{ color: '#64748b', fontSize: '10px', fontWeight: 600 }}
            />
            <Area 
              type="monotone" 
              dataKey="price" 
              stroke="#6366f1" 
              strokeWidth={3}
              fillOpacity={1} 
              fill="url(#colorPrice)" 
              animationDuration={800}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default MarketChart;