
import { OnChainData } from '../types';

export class OnChainAnalyzer {
  static async getMetrics(symbol: string): Promise<OnChainData> {
    // Simulating API latency
    await new Promise(resolve => setTimeout(resolve, 400));
    
    // Generating deterministic mock data based on symbol
    const hash = symbol.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    
    return {
      exchangeNetFlow: (hash % 1000) - 500, // Range -500 to 500
      activeAddresses: 15000 + (hash * 10),
      mvrvRatio: 1.2 + (hash % 100) / 50, // Typical range 1.0 - 3.0
      whaleTransactionCount: 50 + (hash % 150),
      timestamp: Date.now()
    };
  }
}
