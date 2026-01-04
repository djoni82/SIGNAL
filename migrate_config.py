import os
import sys

# Add current directory to path to import config
sys.path.append(os.getcwd())

def migrate():
    try:
        if not os.path.exists('config.py'):
            print("config.py not found. skipping migration.")
            return

        import config
        
        env_content = []
        
        # Telegram
        if hasattr(config, 'TELEGRAM_CONFIG'):
            tc = config.TELEGRAM_CONFIG
            if tc.get('bot_token'): env_content.append(f"TELEGRAM_BOT_TOKEN={tc['bot_token']}")
            if tc.get('chat_id'): env_content.append(f"TELEGRAM_CHAT_ID={tc['chat_id']}")
            if tc.get('admin_chat_id'): env_content.append(f"TELEGRAM_ADMIN_CHAT_ID={tc['admin_chat_id']}")

        # Exchanges
        if hasattr(config, 'EXCHANGE_KEYS'):
            ek = config.EXCHANGE_KEYS
            # Binance
            if ek.get('binance'):
                env_content.append(f"BINANCE_KEY={ek['binance'].get('key', '')}")
                env_content.append(f"BINANCE_SECRET={ek['binance'].get('secret', '')}")
            # Bybit
            if ek.get('bybit'):
                env_content.append(f"BYBIT_KEY={ek['bybit'].get('key', '')}")
                env_content.append(f"BYBIT_SECRET={ek['bybit'].get('secret', '')}")
            # OKX
            if ek.get('okx'):
                env_content.append(f"OKX_KEY={ek['okx'].get('key', '')}")
                env_content.append(f"OKX_SECRET={ek['okx'].get('secret', '')}")
                env_content.append(f"OKX_PASSPHRASE={ek['okx'].get('passphrase', '')}")

        # External APIs
        if hasattr(config, 'EXTERNAL_APIS'):
            ea = config.EXTERNAL_APIS
            if ea.get('dune'):
                env_content.append(f"DUNE_API_KEY={ea['dune'].get('api_key', '')}")
                env_content.append(f"DUNE_QUERY_ID={ea['dune'].get('query_id', '')}")
            if ea.get('crypto_panic'):
                env_content.append(f"CRYPTOPANIC_API_KEY={ea['crypto_panic'].get('api_key', '')}")

        with open('.env', 'w') as f:
            f.write('\n'.join(env_content))
        
        print(f"Successfully migrated {len(env_content)} keys to .env")

    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
