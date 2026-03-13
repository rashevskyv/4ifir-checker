import os
import sys

def verify():
    print("--- Verifying Environment ---")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check dependencies
    try:
        import aiogram
        import telethon
        import requests
        import tqdm
        import pytz
        print("[OK] All dependencies are installed.")
    except ImportError as e:
        print(f"[ERROR] Missing dependency: {e}")
        return False
        
    # Check settings.json or test_settings.json
    config_file = 'test_settings.json' if os.path.exists('test_settings.json') else 'settings.json'
    if not os.path.exists(config_file):
        print(f"[ERROR] Configuration file {config_file} not found.")
        return False
    print(f"[OK] Configuration file {config_file} found.")
    
    # Try to load settings
    try:
        from settings import TELEGRAM_BOT_TOKEN, YOUR_CHAT_ID
        if TELEGRAM_BOT_TOKEN == "os.environ['TELEGRAM_BOT_TOKEN']" and 'TELEGRAM_BOT_TOKEN' not in os.environ:
             print("[WARNING] TELEGRAM_BOT_TOKEN is set to use environment variables, but 'TELEGRAM_BOT_TOKEN' is not set in shell.")
        else:
             print("[OK] Telegram settings loaded.")
    except Exception as e:
        print(f"[ERROR] Failed to load settings: {e}")
        return False
        
    print("[OK] Environment verification complete.")
    return True

if __name__ == "__main__":
    if verify():
        sys.exit(0)
    else:
        sys.exit(1)
