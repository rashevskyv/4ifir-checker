import sys
import json
import os

# Load configuration from a file
def load_config(file, required=True):
    try:
        if not os.path.exists(file):
            if required:
                print(f'Error: configuration file {file} not found.')
                sys.exit(1)
            return None
            
        with open(file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f'Error parsing config file {file}:', e)
        if required:
            sys.exit(1)
        return None
    except Exception as e:
        print(f'Error loading config file {file}:', e)
        if required:
            sys.exit(1)
        return None

# Updated URLs to use GitHub instead of sintez.io
aio_zip_url = ["https://github.com/rashevskyv/4ifir-checker/releases/latest/download/AIO.zip"]
# aio_zip_url = ["http://192.168.50.168/4ifir/AIO.zip"]
aio_zip_path = "aio.zip"
custom_packs_path = "custom_packs.json"
file_to_extract = "config/aio-switch-updater/custom_packs.json"
output_json_path = "custom_packs.json"
archives_output_dir = "archives"  # Змінена директорія виходу

# GitHub API URL for getting release info
github_api_url = "https://api.github.com/repos/rashevskyv/4ifir-checker/releases/latest"

# Load the main configuration from settings.json (required)
settings = load_config('settings.json', required=True)

# Load test configuration for Telegram notifications (optional)
test_settings = load_config('test_settings.json', required=False)

if test_settings:
    print("Test settings loaded successfully for Telegram notifications")
    # Merge test_settings into settings if needed, or keep them separate as before
else:
    print("No test_settings.json found, using only main settings")

# Helper function to get setting value (priority: env var > config file)
def get_setting(key, config):
    val = config.get(key)
    if val == f"os.environ['{key}']":
        return os.environ.get(key, "")
    return val

# Main settings for the application
TELEGRAM_BOT_TOKEN = get_setting('TELEGRAM_BOT_TOKEN', settings)
YOUR_CHAT_ID = get_setting('YOUR_CHAT_ID', settings)
TOPIC_ID = get_setting('TOPIC_ID', settings)
TELEGRAM_API_ID = get_setting('TELEGRAM_API_ID', settings)
TELEGRAM_API_HASH = get_setting('TELEGRAM_API_HASH', settings)
TELEGRAM_USERNAME = get_setting('TELEGRAM_USERNAME', settings)
ENABLE_FILE_UPLOAD_VAL = get_setting('ENABLE_FILE_UPLOAD', settings)
if ENABLE_FILE_UPLOAD_VAL == "" or ENABLE_FILE_UPLOAD_VAL is None:
    ENABLE_FILE_UPLOAD = True
elif isinstance(ENABLE_FILE_UPLOAD_VAL, str):
    ENABLE_FILE_UPLOAD = ENABLE_FILE_UPLOAD_VAL.lower() == 'true'
else:
    ENABLE_FILE_UPLOAD = bool(ENABLE_FILE_UPLOAD_VAL)

# Test settings for Telegram notifications (if available)
if test_settings:
    TEST_TELEGRAM_BOT_TOKEN = get_setting('TELEGRAM_BOT_TOKEN', test_settings)
    TEST_YOUR_CHAT_ID = get_setting('YOUR_CHAT_ID', test_settings)
    TEST_TOPIC_ID = get_setting('TOPIC_ID', test_settings)
    TEST_TELEGRAM_API_ID = get_setting('TELEGRAM_API_ID', test_settings)
    TEST_TELEGRAM_API_HASH = get_setting('TELEGRAM_API_HASH', test_settings)
    TEST_TELEGRAM_USERNAME = get_setting('TELEGRAM_USERNAME', test_settings)
    TEST_ENABLE_FILE_UPLOAD = get_setting('ENABLE_FILE_UPLOAD', test_settings).lower() == 'true' if isinstance(get_setting('ENABLE_FILE_UPLOAD', test_settings), str) else get_setting('ENABLE_FILE_UPLOAD', test_settings)
    if TEST_ENABLE_FILE_UPLOAD is None: TEST_ENABLE_FILE_UPLOAD = ENABLE_FILE_UPLOAD
else:
    # If no test settings, use main settings
    TEST_TELEGRAM_BOT_TOKEN = TELEGRAM_BOT_TOKEN
    TEST_YOUR_CHAT_ID = YOUR_CHAT_ID
    TEST_TOPIC_ID = TOPIC_ID
    TEST_TELEGRAM_API_ID = TELEGRAM_API_ID
    TEST_TELEGRAM_API_HASH = TELEGRAM_API_HASH
    TEST_TELEGRAM_USERNAME = TELEGRAM_USERNAME
    TEST_ENABLE_FILE_UPLOAD = ENABLE_FILE_UPLOAD

report_file = 'README.md'
