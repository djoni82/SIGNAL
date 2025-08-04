#!/usr/bin/env python3
"""
Check Bot Status - Проверка статуса бота
"""

import time
import psutil
import subprocess
import os

def check_bot_status():
    """Проверяет статус бота"""
    print("🔍 Проверка статуса CryptoAlphaPro Bot...")
    
    # Ищем процесс бота
    bot_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'universal_crypto_alpha_bot.py' in ' '.join(proc.info['cmdline'] or []):
                bot_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if bot_processes:
        print("✅ Бот запущен!")
        for proc in bot_processes:
            print(f"   PID: {proc.info['pid']}")
            print(f"   Время запуска: {time.strftime('%H:%M:%S', time.localtime(proc.create_time()))}")
            print(f"   Время работы: {time.time() - proc.create_time():.0f} секунд")
            print(f"   CPU: {proc.cpu_percent():.1f}%")
            print(f"   RAM: {proc.memory_info().rss / 1024 / 1024:.1f} MB")
    else:
        print("❌ Бот не запущен!")
    
    # Проверяем файлы
    print("\n📁 Проверка файлов:")
    files_to_check = [
        'universal_crypto_alpha_bot.py',
        'advanced_ai_engine.py',
        'universal_data_manager.py',
        'signal_explainer.py',
        'advanced_technical_analyzer.py'
    ]
    
    for file in files_to_check:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - отсутствует")
    
    # Проверяем зависимости
    print("\n📦 Проверка зависимостей:")
    try:
        import pandas
        print("   ✅ pandas")
    except ImportError:
        print("   ❌ pandas - не установлен")
    
    try:
        import numpy
        print("   ✅ numpy")
    except ImportError:
        print("   ❌ numpy - не установлен")
    
    try:
        import aiohttp
        print("   ✅ aiohttp")
    except ImportError:
        print("   ❌ aiohttp - не установлен")
    
    try:
        import asyncio
        print("   ✅ asyncio")
    except ImportError:
        print("   ❌ asyncio - не установлен")

def test_signal_generation_time():
    """Тестирует время генерации сигналов"""
    print("\n⏱️ Тестирование времени генерации сигналов...")
    
    start_time = time.time()
    
    try:
        result = subprocess.run([
            'python', 'test_signal_generation.py'
        ], capture_output=True, text=True, timeout=30)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"✅ Тест завершен за {execution_time:.2f} секунд")
        
        if result.stdout:
            print("📊 Результаты:")
            lines = result.stdout.strip().split('\n')
            for line in lines[-5:]:  # Последние 5 строк
                if line.strip():
                    print(f"   {line}")
        
        if result.stderr:
            print("⚠️ Предупреждения:")
            print(f"   {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ Тест превысил лимит времени (30 секунд)")
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")

if __name__ == "__main__":
    check_bot_status()
    test_signal_generation_time()
    
    print("\n🎯 Рекомендации:")
    print("1. Если бот не запущен, выполните: python universal_crypto_alpha_bot.py")
    print("2. Для Telegram бота: python telegram_test_bot.py (замените TOKEN)")
    print("3. Для тестирования: python test_signal_generation.py")
    print("4. Время анализа 343 пар: ~15-20 секунд")
    print("5. Частота обновления: каждые 5 минут") 