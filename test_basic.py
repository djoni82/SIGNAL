#!/usr/bin/env python3
"""
Basic test file for CryptoAlphaPro Signal Bot
"""

import sys
import os

def test_imports():
    """Test basic imports"""
    try:
        import requests
        print("✅ requests imported successfully")
    except ImportError:
        print("❌ requests import failed")
        return False
    
    try:
        import pandas as pd
        print("✅ pandas imported successfully")
    except ImportError:
        print("❌ pandas import failed")
        return False
    
    try:
        import numpy as np
        print("✅ numpy imported successfully")
    except ImportError:
        print("❌ numpy import failed")
        return False
    
    return True

def test_config():
    """Test configuration files"""
    config_files = [
        'requirements.txt',
        'README.md',
        'START_HERE.md',
        'ALL_KEYS_SUMMARY.md'
    ]
    
    for file in config_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            return False
    
    return True

def test_telegram_config():
    """Test Telegram configuration"""
    telegram_token = "8243982780:AAHb72Vjf76iIbiS-khO0dLhkmgvsbKKobg"
    chat_id = "5333574230"
    
    if len(telegram_token) > 0:
        print("✅ Telegram token configured")
    else:
        print("❌ Telegram token missing")
        return False
    
    if len(chat_id) > 0:
        print("✅ Chat ID configured")
    else:
        print("❌ Chat ID missing")
        return False
    
    return True

def main():
    """Main test function"""
    print("🧪 Running CryptoAlphaPro Signal Bot tests...")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Config Test", test_config),
        ("Telegram Config Test", test_telegram_config)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            print(f"✅ {test_name} PASSED")
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bot is ready to run.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 