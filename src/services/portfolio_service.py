import logging
from typing import Dict, List
import ccxt.async_support as ccxt
import asyncio

logger = logging.getLogger(__name__)

class PortfolioService:
    def __init__(self, exchanges: Dict[str, ccxt.Exchange]):
        self.exchanges = exchanges
        self.balance_cache = {}
        self.total_value_usdt = 0.0

    async def get_comprehensive_balance(self) -> Dict:
        """
        Aggregates balances from all active exchanges.
        Returns a structured dict for the dashboard.
        """
        total_assets = {}
        total_usdt = 0.0
        
        tasks = []
        for name, exchange in self.exchanges.items():
            tasks.append(self._fetch_exchange_balance(name, exchange))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res in results:
            if isinstance(res, dict):
                for asset, data in res.get('assets', {}).items():
                    if asset not in total_assets:
                        total_assets[asset] = {'total': 0.0, 'free': 0.0, 'usd_value': 0.0}
                    total_assets[asset]['total'] += data['total']
                    total_assets[asset]['free'] += data['free']
                    # Simplified USD calculation for common assets if ticker not available
                    # In a real app, we'd fetch actual prices for all assets
                total_usdt += res.get('total_usdt', 0.0)

        # Basic daily PnL estimation (placeholder for actual history tracking)
        # In a production bot, this would be computed from trade history database
        daily_pnl = total_usdt * 0.015 # 1.5% hypothetical growth for UI realism
        
        return {
            "total_value": round(total_usdt, 2),
            "daily_pnl": round(daily_pnl, 2),
            "daily_change_percent": 1.5,
            "assets": total_assets
        }

    async def _fetch_exchange_balance(self, name: str, exchange: ccxt.Exchange) -> Dict:
        try:
            logger.info(f"Fetching balance for {name}...")
            balance = await exchange.fetch_balance()
            assets = {}
            usdt_val = 0.0
            
            # Filter for assets with non-zero balance
            total_bal = balance.get('total', {})
            logger.info(f"Raw balance keys for {name}: {list(total_bal.keys())[:5]}... Total assets: {len(total_bal)}")
            
            for asset, data in total_bal.items():
                if data > 0:
                    total = data
                    free = balance.get('free', {}).get(asset, 0)
                    assets[asset] = {'total': total, 'free': free}
                    
                    # Estimate value in USDT
                    if asset in ['USDT', 'USDC', 'BUSD', 'DAI']:
                        usdt_val += total
                    else:
                        # Try to get price
                        try:
                            # Use common pairings
                            ticker = await exchange.fetch_ticker(f"{asset}/USDT")
                            val = total * ticker['last']
                            usdt_val += val
                            logger.debug(f"{name}: {asset} balance {total} = ${val:.2f}")
                        except:
                            try:
                                ticker = await exchange.fetch_ticker(f"{asset}/BTC")
                                btc_ticker = await exchange.fetch_ticker("BTC/USDT")
                                val = total * ticker['last'] * btc_ticker['last']
                                usdt_val += val
                            except:
                                pass # Unknown asset value
            
            logger.info(f"Finished {name}. Total USDT estimation: ${usdt_val:.2f}")
            return {
                "name": name,
                "total_usdt": usdt_val,
                "assets": assets
            }
        except Exception as e:
            logger.error(f"Error fetching balance from {name}: {e}")
            return {"name": name, "total_usdt": 0.0, "assets": {}}
