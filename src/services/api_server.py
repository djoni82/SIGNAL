import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

app = FastAPI(title="SignalPro API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state to share with Bot
bot_instance = None

class BotStatus(BaseModel):
    is_running: bool
    active_exchanges: List[str]
    active_pairs: List[str]
    last_update: str
    signals_count: int

@app.get("/api/status", response_model=BotStatus)
async def get_status():
    if not bot_instance:
        return {
            "is_running": False,
            "active_exchanges": [],
            "active_pairs": [],
            "last_update": "N/A",
            "signals_count": 0
        }
    
    return {
        "is_running": bot_instance.is_running,
        "active_exchanges": list(bot_instance.exchanges.keys()),
        "active_pairs": bot_instance.settings.trading_pairs,
        "last_update": datetime.now().isoformat(),
        "signals_count": len(bot_instance.signal_generator.signal_cache)
    }

@app.get("/api/signals")
async def get_signals():
    if not bot_instance:
        return []
    
    # Return cache from signal generator
    signals = []
    for symbol, (signal, timestamp) in bot_instance.signal_generator.signal_cache.items():
        # Convert signal objects to dicts
        sig_dict = signal.__dict__.copy()
        sig_dict['valid_until'] = sig_dict['valid_until'].isoformat()
        sig_dict['timestamp'] = timestamp.isoformat()
        signals.append(sig_dict)
    
    return signals

@app.post("/api/control/stop")
async def stop_bot():
    if bot_instance:
        bot_instance.is_running = False
        return {"status": "Stopped"}
    return {"status": "Not initialized"}

@app.post("/api/control/start")
async def start_bot():
    if bot_instance:
        bot_instance.is_running = True
        return {"status": "Started"}
    return {"status": "Not initialized"}

def run_api(bot):
    global bot_instance
    bot_instance = bot
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
