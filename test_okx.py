import asyncio
import ccxt.async_support as ccxt
import time

async def test_endpoint(hostname):
    print(f"Testing connectivity to OKX via {hostname}...")
    try:
        exchange = ccxt.okx({
            'hostname': hostname,
            'timeout': 5000,
        })
        start = time.time()
        await exchange.load_markets()
        print(f"✅ Success via {hostname}! Time: {time.time() - start:.2f}s")
        await exchange.close()
        return True
    except Exception as e:
        print(f"❌ Failed via {hostname}: {e}")
        try:
            await exchange.close()
        except:
            pass
        return False

async def main():
    endpoints = ['okx.com', 'aws.okx.com'] # ccxt uses these keys for hostname mapping usually, or we pass the hostname directly if supported
    
    # Direct hostname modification test
    success = False
    
    # Test 1: Default
    print("\n--- Test 1: Default ---")
    try:
        exchange = ccxt.okx()
        await exchange.load_markets()
        print("✅ Default endpoint working")
        await exchange.close()
        success = True
    except Exception as e:
        print(f"❌ Default failed: {e}")
        try: await exchange.close() 
        except: pass

    if success: return

    # Test 2: aws.okx.com
    print("\n--- Test 2: aws.okx.com ---")
    try:
        exchange = ccxt.okx({'hostname': 'aws'}) 
        await exchange.load_markets()
        print("✅ aws.okx.com working")
        await exchange.close()
    except Exception as e:
        print(f"❌ aws.okx.com failed: {e}")
        try: await exchange.close() 
        except: pass

if __name__ == "__main__":
    asyncio.run(main())
