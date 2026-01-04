import React, { useState, useEffect } from 'react';
import { Settings, Play, Square, Circle, Wifi, Activity } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

const BotControl: React.FC = () => {
    const [status, setStatus] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    const fetchStatus = async () => {
        try {
            const res = await fetch(`${API_BASE}/status`);
            const data = await res.json();
            setStatus(data);
        } catch (e) {
            console.error("Failed to fetch bot status", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleControl = async (action: 'start' | 'stop') => {
        try {
            await fetch(`${API_BASE}/control/${action}`, { method: 'POST' });
            fetchStatus();
        } catch (e) {
            alert("Error controlling bot");
        }
    };

    if (loading && !status) return <div className="p-4 text-center text-slate-400">Connecting to Engine...</div>;

    const isRunning = status?.is_running;

    return (
        <div className="bg-slate-900 text-white rounded-3xl p-6 shadow-2xl mb-6 overflow-hidden relative border border-slate-800">
            {/* Background Glow */}
            <div className={`absolute -right-10 -top-10 w-40 h-40 rounded-full blur-3xl opacity-20 ${isRunning ? 'bg-emerald-500' : 'bg-rose-500'}`} />

            <div className="flex justify-between items-center relative z-10 mb-6">
                <div className="flex items-center gap-3">
                    <div className="bg-slate-800 p-2.5 rounded-xl border border-slate-700">
                        <Activity className="w-5 h-5 text-blue-400" />
                    </div>
                    <div>
                        <h2 className="text-lg font-black tracking-tight leading-none">NEURAL CORE v3</h2>
                        <div className="flex items-center gap-1.5 mt-1.5">
                            <Circle className={`w-2.5 h-2.5 fill-current ${isRunning ? 'text-emerald-500' : 'text-rose-500'}`} />
                            <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">
                                {isRunning ? 'System Operational' : 'Standby / Shutdown'}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="flex gap-2">
                    {isRunning ? (
                        <button
                            onClick={() => handleControl('stop')}
                            className="flex items-center gap-2 bg-rose-500 hover:bg-rose-600 text-white px-4 py-2.5 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all active:scale-95"
                        >
                            <Square className="w-3.5 h-3.5 fill-current" /> Stop Bot
                        </button>
                    ) : (
                        <button
                            onClick={() => handleControl('start')}
                            className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-2.5 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all active:scale-95 shadow-lg shadow-emerald-500/20"
                        >
                            <Play className="w-3.5 h-3.5 fill-current" /> Initialize
                        </button>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4 relative z-10">
                <div className="bg-slate-800/50 rounded-2xl p-4 border border-slate-700/50">
                    <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1">Active Gateways</p>
                    <div className="flex flex-wrap gap-2">
                        {status?.active_exchanges?.map((ex: string) => (
                            <span key={ex} className="text-[10px] font-bold text-blue-300 capitalize bg-blue-900/30 px-2 py-0.5 rounded-md border border-blue-500/20">{ex}</span>
                        ))}
                    </div>
                </div>

                <div className="bg-slate-800/50 rounded-2xl p-4 border border-slate-700/50">
                    <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1">Signals in Queue</p>
                    <p className="text-xl font-black text-emerald-400 leading-none">{status?.signals_count || 0}</p>
                </div>
            </div>

            <div className="mt-4 flex items-center gap-2 px-1">
                <Wifi className="w-3 h-3 text-slate-500" />
                <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">
                    Engine Sync: {status?.last_update ? new Date(status.last_update).toLocaleTimeString() : 'Offline'}
                </span>
            </div>
        </div>
    );
};

export default BotControl;
