#!/usr/bin/env python3
"""
CryptoAlphaPro - Startup Script
Простой скрипт для запуска торгового бота
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Добавляем корневую папку в путь
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def print_banner():
    """Красивый баннер для запуска"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🚀 CryptoAlphaPro 🚀                      ║
║                                                              ║
║        🔥 AI-Powered Crypto Trading Bot with 50x Leverage   ║
║        ⚡ Millisecond Signal Generation                      ║
║        🧠 Advanced ML Risk Management                       ║
║        📱 Telegram Remote Control                           ║
║                                                              ║
║        Ready for Professional High-Frequency Trading!       ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_requirements():
    """Проверка основных требований"""
    print("🔍 Checking requirements...")
    
    # Проверка .env файла
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("   Run: ./setup_api_keys.sh first")
        return False
    
    # Проверка конфигурации
    if not os.path.exists('config/config.yaml'):
        print("❌ config/config.yaml not found!")
        return False
    
    # Проверка main.py
    if not os.path.exists('src/main.py'):
        print("❌ src/main.py not found!")
        return False
    
    print("✅ All requirements satisfied")
    return True

def start_with_docker():
    """Запуск через Docker"""
    print("🐳 Starting with Docker...")
    
    try:
        # Проверяем, что Docker доступен
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Docker not found or not running")
            return False
        
        print("✅ Docker available")
        
        # Запуск через docker-compose
        print("🚀 Starting docker-compose...")
        subprocess.run(['docker-compose', 'up', '-d'], check=True)
        
        print("✅ CryptoAlphaPro started with Docker!")
        print("📊 Grafana: http://localhost:3000")
        print("📈 Prometheus: http://localhost:9090")
        print("📱 Check your Telegram bot for signals!")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker startup failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ docker-compose not found")
        return False

def start_manually():
    """Ручной запуск"""
    print("🐍 Starting manually with Python...")
    
    try:
        # Установка зависимостей (если нужно)
        print("📦 Installing dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      capture_output=True)
        
        # Запуск основного приложения
        print("🚀 Starting CryptoAlphaPro...")
        os.chdir(project_root)
        subprocess.run([sys.executable, 'src/main.py'])
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping CryptoAlphaPro...")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_telegram_setup():
    """Показать инструкции для Telegram"""
    print("""
📱 TELEGRAM BOT SETUP:
=====================

1. Your bot: @AlphaSignalProK_bot
2. Get your Chat ID:
   • Send any message to @AlphaSignalProK_bot
   • Visit: https://api.telegram.org/bot8243982780:AAHb72Vjf76iIbiS-khO0dLhkmgvsbKKobg/getUpdates
   • Find "chat":{"id":YOUR_NUMBER} and copy YOUR_NUMBER
   
3. Update .env file:
   • nano .env
   • Change TELEGRAM_CHAT_ID=YOUR_CHAT_ID
   • Change TELEGRAM_ADMIN_CHAT_ID=YOUR_CHAT_ID

4. Available Telegram Commands:
   • /start - Bot info
   • /status - Current status
   • /signals - Recent signals
   • /stats - Trading statistics
   • /startbot - Start trading
   • /stopbot - Stop trading
   • /restart - Restart bot
   • /shutdown - Emergency stop
   • /botcontrol - Control panel

""")

def main():
    """Главная функция"""
    print_banner()
    
    # Проверка требований
    if not check_requirements():
        print("\n❌ Requirements not met. Please setup first:")
        print("   1. Run: ./setup_api_keys.sh")
        print("   2. Update your Telegram Chat ID in .env")
        print("   3. Run this script again")
        return
    
    show_telegram_setup()
    
    # Выбор способа запуска
    print("🚀 CHOOSE STARTUP METHOD:")
    print("1. Docker (Recommended) - Full infrastructure")
    print("2. Manual Python - Direct execution")
    print("3. Show paths only")
    print()
    
    while True:
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            if start_with_docker():
                print("\n🎉 CryptoAlphaPro is running!")
                print("📱 Check your Telegram for signals")
                print("📊 Monitor at http://localhost:3000")
                break
            else:
                print("❌ Docker startup failed, try manual startup")
                
        elif choice == '2':
            start_manually()
            break
            
        elif choice == '3':
            print("\n📂 IMPORTANT PATHS:")
            print(f"   Project Root: {project_root}")
            print(f"   Main Script: {project_root}/src/main.py")
            print(f"   Config: {project_root}/config/config.yaml")
            print(f"   Environment: {project_root}/.env")
            print(f"   Docker: {project_root}/docker-compose.yml")
            print()
            print("🚀 STARTUP COMMANDS:")
            print("   Docker: docker-compose up -d")
            print("   Manual: python src/main.py")
            print("   Logs: docker-compose logs -f crypto_bot")
            print("   Stop: docker-compose down")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3")

if __name__ == "__main__":
    main()
