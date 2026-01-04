import asyncio
import ccxt.async_support as ccxt
from src.core.settings import settings

async def verify():
    print("Verifying Binance Keys...")
    exchange = ccxt.binance({
        'apiKey': settings.binance_key,
        'secret': settings.binance_secret,
        'enableRateLimit': True,
    })

    try:
        # Check if keys are loaded
        if not settings.binance_key or not settings.binance_secret:
            print("❌ Keys are missing in .env!")
            return

        print(f"Key (masked): {settings.binance_key[:4]}...{settings.binance_key[-4:]}")

        # 1. Test Public Request
        print("1. Testing Public Request (fetch_time)...")
        await exchange.fetch_time()
        print("✅ Public Request OK")

        # 2. Test Private Request (fetch_balance)
        print("2. Testing Private Request (fetch_balance)...")
        balance = await exchange.fetch_balance()
        print("✅ Private Request OK. Balance fetched.")
        
    except ccxt.AuthenticationError as e:
        print(f"❌ Authentication Error: {e}")
        print("Hint: Check if API Key and Secret are correct.")
    except ccxt.PermissionDenied as e:
        print(f"❌ Permission Denied: {e}")
        print("Hint: Check 'Enable Reading' or IP restrictions.")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
    finally:
        await exchange.close()

if __name__ == "__main__":
    asyncio.run(verify())
