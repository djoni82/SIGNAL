
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { MarketSignal, SignalType, ChartDataPoint, PortfolioState, ArbitrageOpportunity, EnhancedSignal, MarketRegime, OnChainData, MarketData, AdaptiveIndicators } from './types';
import SignalCard from './components/SignalCard';
import MarketChart from './components/MarketChart';
import PortfolioCard from './components/PortfolioCard';
import ArbitragePanel from './components/ArbitragePanel';
import RiskManager from './components/RiskManager';
import { RealTimeAIEngine } from './services/RealTimeAIEngine';
import { Sparkles, Zap, Activity, Terminal, Bot, ChevronRight, LayoutDashboard, Cpu, Globe, Repeat, AlertTriangle, ShieldCheck, RefreshCw, Cpu as CpuIcon, Clock, ArrowDownCircle, ArrowUpCircle, Network } from 'lucide-react';
import { calculateADX, calculateATR, calculateEMA, calculateRSI, calculateTrendSlope, detectWyckoffPhase } from './utils/technicalIndicators';
import { OnChainAnalyzer } from './services/OnChainAnalyzer';
import BotControl from './components/BotControl';

const TIMEFRAMES = ["15M", "1H", "4H", "1D"];
const SIGNAL_TYPES = ["ALL", ...Object.values(SignalType)];

const API_BASE = 'http://localhost:8000/api';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'signals' | 'arbitrage' | 'portfolio' | 'settings'>('dashboard');
  const [selectedSignal, setSelectedSignal] = useState<MarketSignal | null>(null);
  const [enhancedSignal, setEnhancedSignal] = useState<EnhancedSignal | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [currentRegime, setCurrentRegime] = useState<MarketRegime | null>(null);
  const [onChainMetrics, setOnChainMetrics] = useState<OnChainData | null>(null);

  const [signals, setSignals] = useState<MarketSignal[]>([]);
  const [arbitrageOpportunities] = useState<ArbitrageOpportunity[]>([]);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [engineStatus, setEngineStatus] = useState<'RUNNING' | 'STOPPED' | 'SYNCING'>('RUNNING');
  const [lastSync, setLastSync] = useState<string>('N/A');

  const aiEngine = useMemo(() => new RealTimeAIEngine(), []);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Filter state
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>("1H");
  const [selectedRegime] = useState<string>("ALL");
  const [selectedVolatility] = useState<string>("ALL");

  const [portfolio, setPortfolio] = useState<PortfolioState>({
    totalValue: 0,
    dailyPnL: 0,
    dailyChangePercent: 0,
    positions: []
  });

  const [botStats, setBotStats] = useState({
    winRate: 0,
    totalSignals: 0,
    onChainScore: 'N/A'
  });

  const fetchKlines = async (symbol: string, interval: string = '1h', limit: number = 100): Promise<MarketData[]> => {
    const res = await fetch(`https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval.toLowerCase()}&limit=${limit}`);
    const data = await res.json();
    return data.map((d: any) => ({
      timestamp: d[0],
      open: parseFloat(d[1]),
      high: parseFloat(d[2]),
      low: parseFloat(d[3]),
      close: parseFloat(d[4]),
      volume: parseFloat(d[5])
    }));
  };

  const fetchMarketData = useCallback(async () => {
    setEngineStatus('SYNCING');
    try {
      // 1. Fetch real signals from Python API
      const response = await fetch(`${API_BASE}/signals`);
      if (!response.ok) throw new Error('Engine API fetch failed');
      const apiSignals = await response.json();

      const newSignals: MarketSignal[] = apiSignals.map((sig: any) => ({
        id: sig.symbol.replace('/', ''),
        asset: sig.symbol,
        price: sig.entry_price,
        change24h: 0, // Should be added to API ideally
        type: sig.direction as SignalType,
        strength: sig.confidence,
        onChainScore: sig.on_chain_score || 0.5,
        timestamp: new Date(sig.timestamp).getTime(),
        timeframe: sig.timeframe,
        regime: sig.rationale.regime,
        volatility: sig.rationale.volatility,
        indicators: sig.rationale.indicators || {},
        risk: {
          entry: sig.entry_price,
          stopLoss: sig.stop_loss,
          takeProfit: sig.take_profit,
          trailingStopDistance: sig.trailing_stop_distance || 0,
          rrRatio: `1:${sig.risk_reward.toFixed(1)}`,
          positionSize: sig.position_size_pct,
          expectedValue: sig.expected_value
        }
      }));

      setSignals(newSignals);

      setSignals(newSignals);

      // 2. Fetch Portfolio
      const portResponse = await fetch(`${API_BASE}/portfolio`);
      if (portResponse.ok) {
        const portData = await portResponse.json();
        setPortfolio({
          totalValue: portData.total_value,
          dailyPnL: portData.daily_pnl,
          dailyChangePercent: portData.daily_change_percent,
          positions: Object.entries(portData.assets).map(([asset, data]: [string, any]) => ({
            asset,
            amount: data.total,
            entryPrice: 0, // Not available in current API
            currentPrice: 0 // Not available in current API
          }))
        });
      }

      // 3. Fetch Stats
      const statsResponse = await fetch(`${API_BASE}/stats`);
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setBotStats({
          winRate: statsData.win_rate,
          totalSignals: statsData.total_signals,
          onChainScore: statsData.on_chain_score
        });
      }

      // 4. Fetch Market History for Chart
      const chartSymbol = newSignals.length > 0 ? newSignals[0].asset : 'BTC/USDT';
      const histResponse = await fetch(`${API_BASE}/market/history?symbol=${chartSymbol.replace('/', '_')}`);
      if (histResponse.ok) {
        const histData = await histResponse.json();
        setChartData(histData.map((d: any) => ({
          time: new Date(d.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          price: d.close
        })));
      }

      setLastSync(new Date().toLocaleTimeString());
      setIsLoading(false);
      setEngineStatus('RUNNING');
    } catch (error) {
      console.error('Failed to sync with Engine:', error);
      setEngineStatus('STOPPED');
    }
  }, []);

  useEffect(() => {
    fetchMarketData();
    timerRef.current = setInterval(fetchMarketData, 10000);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [fetchMarketData]);

  const handleStart = () => setEngineStatus('RUNNING');
  const handleStop = () => setEngineStatus('STOPPED');
  const handleReload = () => fetchMarketData();

  const filteredSignals = useMemo(() => {
    return signals.filter(s => {
      const typeMatch = selectedType === "ALL" || s.type === selectedType;
      const timeframeMatch = s.timeframe === selectedTimeframe;
      const regimeMatch = selectedRegime === "ALL" || s.regime === selectedRegime;
      const volatilityMatch = selectedVolatility === "ALL" || s.volatility === selectedVolatility;
      return typeMatch && timeframeMatch && regimeMatch && volatilityMatch;
    });
  }, [signals, selectedType, selectedTimeframe, selectedRegime, selectedVolatility]);

  const handleOpenSignal = async (signal: MarketSignal) => {
    setSelectedSignal(signal);
    setEnhancedSignal(null);
    setIsAnalyzing(true);
    setAnalysisError(null);
    setOnChainMetrics(null);

    try {
      const klines = await fetchKlines(signal.id, '1h', 100);
      const ocData = await OnChainAnalyzer.getMetrics(signal.id);
      setOnChainMetrics(ocData);

      const adx = calculateADX(klines);
      const slope = calculateTrendSlope(klines.map(d => d.close));
      const atr = calculateATR(klines);
      const phase = detectWyckoffPhase(klines);

      const regime: MarketRegime = {
        trend: adx > 25 ? (slope > 0 ? 'bullish' : 'bearish') : 'neutral',
        strength: adx,
        volatility: atr / signal.price > 0.05 ? 'panic' : atr / signal.price > 0.03 ? 'high' : 'medium',
        volatilityValue: (atr / signal.price) * 100,
        btcCorrelation: 0.85,
        phase,
        crisisMode: atr / signal.price > 0.05
      };

      setCurrentRegime(regime);

      const prices = klines.map(d => d.close);
      const emaShort = calculateEMA(prices, 12);
      const emaLong = calculateEMA(prices, 26);
      const indicators: AdaptiveIndicators = {
        rsi: { value: calculateRSI(prices), period: 14 },
        bollinger: { upper: 0, middle: 0, lower: 0, width: 0 },
        ema: { short: emaShort, long: emaLong },
        macd: { value: emaShort - emaLong, signal: 0, histogram: 0 },
        adx,
        atr,
        timestamp: Date.now()
      };

      const result = await aiEngine.processSymbol(signal.id, klines, regime, indicators, ocData);
      setEnhancedSignal(result);
    } catch (err: any) {
      console.error("Deep Scan Neural Error:", err);
      setAnalysisError(err.message || "Uplink failure during deep neural probe.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#fcfcfd] pb-32 flex flex-col antialiased">
      <header className="sticky top-0 z-40 bg-white/80 ios-blur safe-top border-b border-gray-100/50">
        <div className="px-6 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-xl font-black text-slate-900 tracking-tighter">
              {activeTab === 'dashboard' ? 'PULSE' : activeTab.toUpperCase()}
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <div className={`w-2 h-2 rounded-full ${engineStatus === 'RUNNING' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`}></div>
              <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none">
                {engineStatus} • {lastSync}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center shadow-sm">
              <Sparkles size={16} className="text-indigo-600" />
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 px-6 pt-6 overflow-x-hidden max-w-2xl mx-auto w-full">
        {activeTab === 'dashboard' && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <BotControl />
            <PortfolioCard data={portfolio} />
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-white p-4 rounded-[1.5rem] border border-gray-100 flex flex-col items-center gap-2 shadow-sm">
                <div className="w-8 h-8 rounded-xl bg-indigo-50 flex items-center justify-center">
                  <Zap className="w-4 h-4 text-indigo-500" />
                </div>
                <div className="text-center">
                  <p className="text-[7px] font-black text-slate-400 uppercase tracking-wider">Signals</p>
                  <p className="text-xs font-black text-slate-900">{signals.length * 3}</p>
                </div>
              </div>
              <div className="bg-white p-4 rounded-[1.5rem] border border-gray-100 flex flex-col items-center gap-2 shadow-sm">
                <div className="w-8 h-8 rounded-xl bg-emerald-50 flex items-center justify-center">
                  <Activity className="w-4 h-4 text-emerald-500" />
                </div>
                <div className="text-center">
                  <p className="text-[7px] font-black text-slate-400 uppercase tracking-wider">Win Rate</p>
                  <p className="text-xs font-black text-slate-900">{botStats.winRate}%</p>
                </div>
              </div>
              <div className="bg-white p-4 rounded-[1.5rem] border border-gray-100 flex flex-col items-center gap-2 shadow-sm">
                <div className="w-8 h-8 rounded-xl bg-cyan-50 flex items-center justify-center">
                  <Globe className="w-4 h-4 text-cyan-500" />
                </div>
                <div className="text-center">
                  <p className="text-[7px] font-black text-slate-400 uppercase tracking-wider">On-Chain</p>
                  <p className="text-xs font-black text-slate-900">{botStats.onChainScore} Score</p>
                </div>
              </div>
            </div>

            <section>
              <div className="flex justify-between items-center mb-4 px-1">
                <h2 className="text-lg font-black tracking-tight text-slate-900">Market Momentum</h2>
                <div className="flex items-center gap-1.5 text-[9px] font-black text-indigo-600 uppercase tracking-widest">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-ping"></span>
                  Live Feed
                </div>
              </div>
              <div className="bg-white p-4 rounded-[2.5rem] border border-gray-100 shadow-sm">
                <MarketChart data={chartData} />
              </div>
            </section>

            <section>
              <div className="flex justify-between items-center mb-4 px-1">
                <h2 className="text-lg font-black tracking-tight text-slate-900">Institutional Alerts</h2>
                <button onClick={() => setActiveTab('signals')} className="text-[10px] font-black text-indigo-600 bg-indigo-50 px-4 py-1.5 rounded-full uppercase tracking-widest">View All</button>
              </div>
              <div className="space-y-3">
                {signals.slice(0, 3).map(s => (
                  <SignalCard key={s.id} signal={s} onClick={handleOpenSignal} />
                ))}
              </div>
            </section>
          </div>
        )}

        {activeTab === 'signals' && (
          <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
            <div className="flex gap-2 p-1.5 bg-gray-100/50 rounded-2xl border border-gray-200/20 backdrop-blur-md">
              <button onClick={handleStart} className={`flex-1 py-3 rounded-xl text-[9px] font-black tracking-widest uppercase transition-all ${engineStatus === 'RUNNING' ? 'bg-white text-emerald-600 shadow-sm' : 'text-slate-400'}`}>START</button>
              <button onClick={handleStop} className={`flex-1 py-3 rounded-xl text-[9px] font-black tracking-widest uppercase transition-all ${engineStatus === 'STOPPED' ? 'bg-white text-rose-600 shadow-sm' : 'text-slate-400'}`}>STOP</button>
              <button onClick={handleReload} className={`flex-1 py-3 rounded-xl text-[9px] font-black tracking-widest uppercase transition-all ${engineStatus === 'SYNCING' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400'}`}>SYNC</button>
            </div>
            <div className="bg-white p-6 rounded-[2.5rem] border border-gray-100 shadow-sm space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-3">
                  <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Scan Timeframe</p>
                  <div className="flex p-1.5 bg-gray-50 rounded-2xl">
                    {TIMEFRAMES.map(tf => (
                      <button key={tf} onClick={() => setSelectedTimeframe(tf)} className={`flex-1 py-2 rounded-xl text-[9px] font-black transition-all ${selectedTimeframe === tf ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-400'}`}>{tf}</button>
                    ))}
                  </div>
                </div>
                <div className="space-y-3">
                  <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Signal Logic</p>
                  <select value={selectedType} onChange={(e) => setSelectedType(e.target.value)} className="w-full bg-gray-50 rounded-2xl px-4 py-2.5 text-[10px] font-black text-slate-600 outline-none border-none appearance-none cursor-pointer">
                    {SIGNAL_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
              </div>
            </div>
            <div className="space-y-3">
              <h2 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4 px-1">Active Alpha Scans ({filteredSignals.length})</h2>
              {filteredSignals.map(s => <SignalCard key={s.id} signal={s} onClick={handleOpenSignal} />)}
            </div>
          </div>
        )}

        {activeTab === 'arbitrage' && <ArbitragePanel opportunities={arbitrageOpportunities} onExecute={(opp) => alert(`Executing ${opp.type}`)} />}

        {activeTab === 'portfolio' && (
          <div className="space-y-6 animate-in fade-in slide-in-from-left-4 duration-500">
            <div className="bg-white rounded-[3rem] p-8 border border-gray-100 shadow-sm">
              <h3 className="text-sm font-black uppercase text-slate-900 tracking-[0.15em] mb-10">Live Positions</h3>
              <div className="space-y-8">
                {portfolio.positions.map(pos => (
                  <div key={pos.asset} className="flex justify-between items-center group">
                    <div className="flex items-center gap-4">
                      <div className="w-14 h-14 rounded-2xl bg-slate-50 border border-gray-100 flex items-center justify-center font-black text-xl text-slate-300">
                        {pos.asset[0]}
                      </div>
                      <div>
                        <p className="font-black text-slate-900 text-lg tracking-tight">{pos.asset}/USDT</p>
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{pos.amount} Units</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-black text-slate-900 text-lg tracking-tight mono">${(pos.currentPrice * pos.amount).toLocaleString()}</p>
                      <p className="text-[9px] font-black text-emerald-500 uppercase tracking-widest bg-emerald-50 px-2 py-0.5 rounded">LONG</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Deep Neural Scan Detail Bottom Sheet */}
      {selectedSignal && (
        <div className="fixed inset-0 z-50 flex items-end justify-center px-4">
          <div className="absolute inset-0 bg-slate-900/60 ios-blur transition-opacity" onClick={() => setSelectedSignal(null)}></div>
          <div className="relative w-full max-w-lg bg-white rounded-t-[4.5rem] p-8 pb-12 shadow-2xl animate-in slide-in-from-bottom duration-500 overflow-y-auto max-h-[96vh] scrollbar-hide border-t border-white/10">
            <div className="w-16 h-1.5 bg-gray-200/50 rounded-full mx-auto mb-10"></div>

            <div className="flex justify-between items-center mb-10">
              <div className="flex items-center gap-6">
                <div className="w-16 h-16 rounded-[2rem] bg-slate-900 flex items-center justify-center shadow-2xl ring-4 ring-slate-100">
                  <span className="text-white font-black text-2xl">{selectedSignal.asset[0]}</span>
                </div>
                <div>
                  <h3 className="text-4xl font-black tracking-tighter text-slate-900">{selectedSignal.asset}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[10px] px-3 py-1.5 bg-slate-100 rounded-xl font-black text-slate-500 uppercase tracking-[0.1em]">DEEP NEURAL PROBE • {selectedSignal.timeframe}</span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <p className="text-3xl font-black text-slate-900 mono tracking-tighter">${selectedSignal.price.toLocaleString()}</p>
                <p className={`text-[12px] font-black uppercase tracking-widest ${selectedSignal.change24h >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                  {selectedSignal.change24h >= 0 ? '▲' : '▼'} {Math.abs(selectedSignal.change24h).toFixed(2)}%
                </p>
              </div>
            </div>

            {isAnalyzing ? (
              <div className="py-24 text-center space-y-8">
                <div className="relative w-20 h-20 mx-auto">
                  <div className="absolute inset-0 border-4 border-indigo-100 rounded-full"></div>
                  <div className="absolute inset-0 border-t-4 border-indigo-600 rounded-full animate-spin"></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Cpu size={24} className="text-indigo-600 animate-pulse" />
                  </div>
                </div>
                <div>
                  <p className="text-lg font-black text-slate-900 uppercase tracking-[0.2em] mb-2">Neural Synthesis Active</p>
                  <p className="text-xs text-slate-400 font-medium italic">Correlating On-Chain Flows & Market Alpha...</p>
                </div>
              </div>
            ) : enhancedSignal ? (
              <div className="space-y-10 animate-in fade-in duration-700">
                {/* Confidence & Score Metrics */}
                <div className="grid grid-cols-2 gap-5">
                  <div className="p-8 bg-slate-50 rounded-[2.5rem] border border-gray-100 group transition-all hover:bg-white hover:shadow-xl">
                    <div className="flex items-center gap-2 mb-3">
                      <ShieldCheck className="w-4 h-4 text-emerald-500" />
                      <p className="text-[11px] font-black text-slate-400 uppercase tracking-widest">Neural Confidence</p>
                    </div>
                    <p className={`text-4xl font-black tracking-tighter ${enhancedSignal.direction.includes('BUY') ? 'text-emerald-600' : 'text-rose-600'}`}>
                      {enhancedSignal.confidence.toFixed(0)}%
                    </p>
                    <p className="text-[10px] font-black text-slate-400 uppercase mt-2 tracking-widest">{enhancedSignal.direction.replace('_', ' ')}</p>
                  </div>
                  <div className="p-8 bg-slate-50 rounded-[2.5rem] border border-gray-100 group transition-all hover:bg-white hover:shadow-xl">
                    <div className="flex items-center gap-2 mb-3">
                      <Network className="w-4 h-4 text-indigo-500" />
                      <p className="text-[11px] font-black text-slate-400 uppercase tracking-widest">On-Chain Health</p>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <p className="text-4xl font-black text-indigo-600">{(enhancedSignal.onChainScore * 100).toFixed(0)}%</p>
                    </div>
                    <p className="text-[10px] font-black text-slate-400 uppercase mt-2 tracking-widest">Speculative Bias</p>
                  </div>
                </div>

                {/* On-Chain Quick Glance Metrics */}
                {onChainMetrics && (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-[#1c2128] border border-slate-800 rounded-3xl p-5 flex items-center justify-between">
                      <div>
                        <p className="text-[9px] font-black text-slate-500 uppercase mb-1">Exchange Flow</p>
                        <p className={`text-sm font-black mono ${onChainMetrics.exchangeNetFlow < 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {onChainMetrics.exchangeNetFlow > 0 ? '+' : ''}{onChainMetrics.exchangeNetFlow} Net
                        </p>
                      </div>
                      {onChainMetrics.exchangeNetFlow < 0 ? <ArrowDownCircle className="text-emerald-400" /> : <ArrowUpCircle className="text-rose-400" />}
                    </div>
                    <div className="bg-[#1c2128] border border-slate-800 rounded-3xl p-5 flex items-center justify-between">
                      <div>
                        <p className="text-[9px] font-black text-slate-500 uppercase mb-1">Whale Activity</p>
                        <p className="text-sm font-black text-indigo-400 mono">
                          {onChainMetrics.whaleTransactionCount} Tx
                        </p>
                      </div>
                      <Activity className="text-indigo-400" />
                    </div>
                  </div>
                )}

                {/* Granular Institutional Rationale Panel */}
                <div className="bg-[#0b0e14] rounded-[3.5rem] p-10 text-slate-100 shadow-2xl relative overflow-hidden group border border-white/5">
                  <div className="absolute top-0 right-0 p-8 opacity-[0.05] group-hover:opacity-[0.08] transition-opacity">
                    <Bot size={160} />
                  </div>
                  <div className="relative z-10 space-y-10">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse shadow-[0_0_10px_rgba(99,102,241,0.8)]"></div>
                      <h4 className="text-[12px] font-black uppercase tracking-[0.4em] text-slate-400">Quantitative Neural Synthesis</h4>
                    </div>

                    <div className="grid grid-cols-1 gap-10">
                      {/* ML & MTF Section */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                        <section className="space-y-4">
                          <div className="flex items-center gap-2">
                            <CpuIcon size={14} className="text-emerald-400" />
                            <h5 className="text-[10px] font-black uppercase tracking-widest text-emerald-400">ML Consensus & Conflict</h5>
                          </div>
                          <p className="text-sm text-slate-300 leading-relaxed font-medium">{enhancedSignal.rationale.mlModelConsensus}</p>
                          <div className="bg-emerald-500/5 p-4 rounded-2xl border border-emerald-500/10">
                            <p className="text-[8px] font-black text-emerald-600 uppercase mb-2 tracking-widest">Conflict Resolution Strategy</p>
                            <p className="text-xs text-slate-400 italic leading-relaxed">{enhancedSignal.rationale.mlConflictResolution}</p>
                          </div>
                        </section>

                        <section className="space-y-4">
                          <div className="flex items-center gap-2">
                            <Clock size={14} className="text-amber-400" />
                            <h5 className="text-[10px] font-black uppercase tracking-widest text-amber-400">MTF Alignment Matrix</h5>
                          </div>
                          <div className="bg-amber-500/5 p-5 rounded-[2rem] border border-amber-500/20 shadow-inner">
                            <div className="flex items-center gap-2 mb-4">
                              <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></div>
                              <p className="text-[9px] font-black text-amber-500 uppercase tracking-widest">Cross-Timeframe Matrix (15m/1h/4h)</p>
                            </div>
                            <div className="space-y-4">
                              <p className="text-xs text-slate-300 leading-relaxed font-medium bg-[#161b22] p-3 rounded-xl border border-slate-800 mono text-[10px]">{enhancedSignal.rationale.mtfCrossTimeframeMatrix}</p>
                              <div className="pt-2 border-t border-slate-800">
                                <p className="text-[8px] font-black text-slate-500 uppercase mb-1 tracking-widest">MTF Logic Breakdown</p>
                                <p className="text-[11px] text-slate-400 italic leading-relaxed">{enhancedSignal.rationale.mtfLogic}</p>
                              </div>
                            </div>
                          </div>
                          <p className="text-sm text-slate-300 leading-relaxed font-medium">{enhancedSignal.rationale.mtfAlignmentAnalysis}</p>
                        </section>
                      </div>

                      {/* On-Chain Deep Dive */}
                      <section className="pt-10 border-t border-slate-800 space-y-5">
                        <div className="flex items-center gap-2">
                          <Network size={14} className="text-cyan-400" />
                          <h5 className="text-[10px] font-black uppercase tracking-widest text-cyan-400">On-Chain Flow Dynamics</h5>
                        </div>
                        <p className="text-sm text-slate-200 leading-relaxed font-semibold">{enhancedSignal.rationale.onChainFlowDynamics}</p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div className="bg-[#161b22] p-6 rounded-[2rem] border border-slate-800">
                            <p className="text-[9px] font-black text-slate-500 uppercase mb-3 tracking-widest">Synthesis Interpretation</p>
                            <p className="text-xs text-slate-400 leading-relaxed italic">{enhancedSignal.rationale.onChainInterp}</p>
                          </div>
                          <div className="bg-[#161b22] p-6 rounded-[2rem] border border-slate-800">
                            <p className="text-[9px] font-black text-slate-500 uppercase mb-3 tracking-widest">Score Allocation Logic</p>
                            <p className="text-xs text-slate-400 leading-relaxed italic">{enhancedSignal.rationale.onChainScoreLogic}</p>
                          </div>
                        </div>
                      </section>
                    </div>
                  </div>
                </div>

                {/* Advanced Risk Manager Component */}
                {currentRegime && (
                  <RiskManager
                    signal={enhancedSignal}
                    regime={currentRegime}
                    totalCapital={portfolio.totalValue}
                  />
                )}

                <button className="w-full bg-slate-900 text-white py-8 rounded-[3rem] font-black text-xl shadow-2xl active:scale-[0.97] transition-all flex items-center justify-center gap-5 hover:bg-black group">
                  <span className="tracking-tighter">EXECUTE NEURAL TRADE LOGIC</span>
                  <ChevronRight size={24} className="group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            ) : analysisError ? (
              <div className="py-24 text-center px-6">
                <div className="w-24 h-24 bg-rose-50 rounded-[3rem] flex items-center justify-center mx-auto mb-8 ring-8 ring-rose-50/50">
                  <AlertTriangle size={40} className="text-rose-500" />
                </div>
                <p className="text-xl font-black text-slate-900 uppercase tracking-widest mb-3">Probe Sequence Interrupted</p>
                <p className="text-sm text-slate-500 mb-10 leading-relaxed italic max-w-sm mx-auto">"{analysisError}"</p>
                <button
                  onClick={() => handleOpenSignal(selectedSignal!)}
                  className="flex items-center gap-3 px-10 py-5 bg-slate-900 text-white rounded-[2rem] mx-auto text-xs font-black uppercase tracking-[0.2em] active:scale-95 transition-all shadow-2xl shadow-slate-900/20"
                >
                  <RefreshCw size={18} /> Restart Neural Scan
                </button>
              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* Tab Bar */}
      <nav className="fixed bottom-0 inset-x-0 bg-white/95 ios-blur safe-bottom border-t border-gray-100/50 z-40">
        <div className="flex justify-around items-center h-20 px-6">
          <button onClick={() => setActiveTab('dashboard')} className={`flex flex-col items-center gap-1 ${activeTab === 'dashboard' ? 'text-indigo-600' : 'text-slate-300'}`}>
            <LayoutDashboard size={22} />
            <span className="text-[8px] font-black uppercase">Pulse</span>
          </button>
          <button onClick={() => setActiveTab('signals')} className={`flex flex-col items-center gap-1 ${activeTab === 'signals' ? 'text-indigo-600' : 'text-slate-300'}`}>
            <Zap size={22} />
            <span className="text-[8px] font-black uppercase">Alerts</span>
          </button>
          <button onClick={() => setActiveTab('arbitrage')} className={`flex flex-col items-center gap-1 ${activeTab === 'arbitrage' ? 'text-indigo-600' : 'text-slate-300'}`}>
            <Repeat size={22} />
            <span className="text-[8px] font-black uppercase">Arb</span>
          </button>
          <button onClick={() => setActiveTab('portfolio')} className={`flex flex-col items-center gap-1 ${activeTab === 'portfolio' ? 'text-indigo-600' : 'text-slate-300'}`}>
            <Terminal size={22} />
            <span className="text-[8px] font-black uppercase">Assets</span>
          </button>
        </div>
      </nav>
    </div>
  );
};

export default App;
