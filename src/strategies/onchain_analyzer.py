import asyncio
import time
import random
from dataclasses import dataclass

@dataclass
class OnChainData:
    exchange_net_flow: float
    active_addresses: int
    mvrv_ratio: float
    whale_transaction_count: int
    timestamp: float

class OnChainAnalyzer:
    """
    Simulates fetching on-chain metrics. In a real production environment, 
    this would call Glassnode, CryptoQuant, or Dune API.
    """
    
    @staticmethod
    async def get_metrics(symbol: str) -> OnChainData:
        # Simulate API latency
        await asyncio.sleep(0.4)
        
        # Deterministic pseudo-mock data based on symbol name
        hash_val = sum(ord(c) for c in symbol)
        
        # Simulated metrics
        return OnChainData(
            exchange_net_flow=(hash_val % 1000) - 500,  # Range -500 to 500
            active_addresses=15000 + (hash_val * 10),
            mvrv_ratio=1.2 + (hash_val % 100) / 50.0,   # 1.0 - 3.0
            whale_transaction_count=50 + (hash_val % 150),
            timestamp=time.time()
        )
