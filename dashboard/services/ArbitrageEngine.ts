import { ArbitrageOpportunity, MarketSignal } from '../types';

export class ArbitrageEngine {
  static detect(signals: MarketSignal[]): ArbitrageOpportunity[] {
    const opportunities: ArbitrageOpportunity[] = [];

    // 1. Simulate Cross-Exchange Arbitrage (Binance vs Kraken mock)
    signals.forEach(s => {
      // Randomly simulate a price spread of 0.1% to 0.5%
      const spread = (Math.random() * 0.4 + 0.1) / 100;
      const profitPct = spread * 100;
      
      if (profitPct > 0.2) {
        opportunities.push({
          id: `cross-${s.id}-${Date.now()}`,
          type: 'Cross-Exchange',
          asset: s.asset,
          profitPct: profitPct,
          expectedProfit: 50 + Math.random() * 200,
          executionRisk: profitPct > 0.4 ? 'High' : 'Medium',
          venues: ['Binance', 'Kraken'],
          spread: spread * s.price,
          timestamp: Date.now()
        });
      }
    });

    // 2. Simulate Triangular Arbitrage (e.g., BTC -> ETH -> USDT -> BTC)
    const btc = signals.find(s => s.id === 'BTCUSDT');
    const eth = signals.find(s => s.id === 'ETHUSDT');
    
    if (btc && eth) {
      const triangularProfit = (Math.random() * 0.3 + 0.05);
      if (triangularProfit > 0.15) {
        opportunities.push({
          id: `tri-${Date.now()}`,
          type: 'Triangular',
          asset: 'BTC/ETH/USDT',
          path: ['BTC', 'ETH', 'USDT'],
          profitPct: triangularProfit,
          expectedProfit: 120 + Math.random() * 300,
          executionRisk: 'Low',
          venues: ['Binance'],
          spread: triangularProfit / 100 * btc.price,
          timestamp: Date.now()
        });
      }
    }

    return opportunities.sort((a, b) => b.profitPct - a.profitPct);
  }
}
