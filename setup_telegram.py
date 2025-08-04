#!/usr/bin/env python3
"""
Setup Telegram - Настройка Telegram бота
"""

import os
import sys

def setup_telegram():
    """Настройка Telegram бота"""
    print("🤖 Настройка Telegram для CryptoAlphaPro Bot")
    print("=" * 50)
    
    # Проверяем текущие настройки
    try:
        from config import TELEGRAM_CONFIG
        current_token = TELEGRAM_CONFIG['bot_token']
        current_chat_id = TELEGRAM_CONFIG['chat_id']
        
        print(f"📱 Текущий токен: {current_token}")
        print(f"💬 Текущий chat_id: {current_chat_id}")
        print()
        
    except ImportError:
        print("❌ Файл config.py не найден!")
        return False
    
    # Запрашиваем новые настройки
    print("📝 Введите новые настройки Telegram:")
    print()
    
    # Токен бота
    new_token = input("🔑 Введите токен бота (или Enter для пропуска): ").strip()
    if new_token:
        TELEGRAM_CONFIG['bot_token'] = new_token
        print("✅ Токен обновлен")
    
    # Chat ID
    new_chat_id = input("💬 Введите chat_id (или Enter для пропуска): ").strip()
    if new_chat_id:
        TELEGRAM_CONFIG['chat_id'] = new_chat_id
        print("✅ Chat ID обновлен")
    
    # Обновляем config.py
    try:
        update_config_file()
        print("✅ Файл config.py обновлен")
        return True
    except Exception as e:
        print(f"❌ Ошибка обновления config.py: {e}")
        return False

def update_config_file():
    """Обновляет файл config.py с новыми настройками"""
    from config import TELEGRAM_CONFIG, TRADING_CONFIG, ANALYSIS_CONFIG
    
    config_content = f'''#!/usr/bin/env python3
"""
Configuration - Конфигурация для CryptoAlphaPro Bot
"""

# Telegram настройки
TELEGRAM_CONFIG = {{
    'bot_token': '{TELEGRAM_CONFIG['bot_token']}',
    'chat_id': '{TELEGRAM_CONFIG['chat_id']}',
    'enable_telegram': {TELEGRAM_CONFIG['enable_telegram']},
    'send_signals': {TELEGRAM_CONFIG['send_signals']},
    'send_status': {TELEGRAM_CONFIG['send_status']},
    'send_errors': {TELEGRAM_CONFIG['send_errors']},
}}

# Торговые настройки
TRADING_CONFIG = {{
    'pairs': {TRADING_CONFIG['pairs']},
    'timeframes': {TRADING_CONFIG['timeframes']},
    'update_frequency': {TRADING_CONFIG['update_frequency']},
    'min_confidence': {TRADING_CONFIG['min_confidence']},
    'top_signals': {TRADING_CONFIG['top_signals']}
}}

# Анализ настройки
ANALYSIS_CONFIG = {{
    'min_confidence': {ANALYSIS_CONFIG['min_confidence']},
    'min_risk_reward': {ANALYSIS_CONFIG['min_risk_reward']},
    'max_signals_per_cycle': {ANALYSIS_CONFIG['max_signals_per_cycle']}
}}
'''
    
    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(config_content)

def test_telegram_connection():
    """Тестирует подключение к Telegram"""
    print("\n🧪 Тестирование подключения к Telegram...")
    
    try:
        from telegram_integration import TelegramIntegration
        import asyncio
        
        async def test():
            telegram = TelegramIntegration()
            if telegram.bot_token == 'YOUR_TELEGRAM_BOT_TOKEN':
                print("❌ Токен бота не настроен!")
                return False
            
            if telegram.chat_id == 'YOUR_CHAT_ID':
                print("❌ Chat ID не настроен!")
                return False
            
            # Тестируем отправку сообщения
            test_message = "🧪 Тестовое сообщение от CryptoAlphaPro Bot"
            success = await telegram.send_message(test_message)
            
            if success:
                print("✅ Подключение к Telegram успешно!")
                return True
            else:
                print("❌ Ошибка отправки сообщения в Telegram")
                return False
        
        return asyncio.run(test())
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def get_telegram_help():
    """Показывает справку по настройке Telegram"""
    print("\n📚 Справка по настройке Telegram:")
    print("=" * 40)
    print("1. Создайте бота в Telegram:")
    print("   • Найдите @BotFather в Telegram")
    print("   • Отправьте команду /newbot")
    print("   • Следуйте инструкциям")
    print("   • Скопируйте полученный токен")
    print()
    print("2. Получите ваш Chat ID:")
    print("   • Найдите @userinfobot в Telegram")
    print("   • Отправьте любое сообщение")
    print("   • Скопируйте ваш ID")
    print()
    print("3. Настройте бота:")
    print("   • Запустите этот скрипт: python setup_telegram.py")
    print("   • Введите токен и chat_id")
    print()
    print("4. Протестируйте:")
    print("   • Запустите: python test_telegram.py")

def main():
    """Главная функция"""
    print("🚀 CryptoAlphaPro Bot - Настройка Telegram")
    print("=" * 50)
    
    while True:
        print("\nВыберите действие:")
        print("1. Настроить Telegram")
        print("2. Протестировать подключение")
        print("3. Показать справку")
        print("4. Выход")
        
        choice = input("\nВведите номер (1-4): ").strip()
        
        if choice == '1':
            setup_telegram()
        elif choice == '2':
            test_telegram_connection()
        elif choice == '3':
            get_telegram_help()
        elif choice == '4':
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор!")

if __name__ == "__main__":
    main() 