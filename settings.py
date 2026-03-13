import sys
import json
import os

# Load configuration from a file
def load_config(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f'Error loading config file {file}:', e)
        sys.exit(1)

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

# Load the main configuration from settings.json
# settings = load_config('settings.json')
settings = load_config('test_settings.json')

# Load test configuration for Telegram notifications
test_settings = None
try:
    test_settings = load_config('test_settings.json')
    print("Test settings loaded successfully for Telegram notifications")
except Exception as e:
    print(f"Warning: Could not load test_settings.json: {e}")
    print("Will use main settings for Telegram notifications")

# Main settings for the application
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN'] if settings['TELEGRAM_BOT_TOKEN'] == "os.environ['TELEGRAM_BOT_TOKEN']" else settings['TELEGRAM_BOT_TOKEN']
YOUR_CHAT_ID = os.environ['YOUR_CHAT_ID'] if settings['YOUR_CHAT_ID'] == "os.environ['YOUR_CHAT_ID']" else settings['YOUR_CHAT_ID']
TOPIC_ID = os.environ['TOPIC_ID'] if settings['TOPIC_ID'] == "os.environ['TOPIC_ID']" else settings['TOPIC_ID']
TELEGRAM_API_ID = os.environ['TELEGRAM_API_ID'] if settings['TELEGRAM_API_ID'] == "os.environ['TELEGRAM_API_ID']" else settings['TELEGRAM_API_ID']
TELEGRAM_API_HASH = os.environ['TELEGRAM_API_HASH'] if settings['TELEGRAM_API_HASH'] == "os.environ['TELEGRAM_API_HASH']" else settings['TELEGRAM_API_HASH']
TELEGRAM_USERNAME = os.environ['TELEGRAM_USERNAME'] if settings['TELEGRAM_USERNAME'] == "os.environ['TELEGRAM_USERNAME']" else settings['TELEGRAM_USERNAME']

# Test settings for Telegram notifications (if available)
if test_settings:
    # Override Telegram settings with test values
    TEST_TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN'] if test_settings['TELEGRAM_BOT_TOKEN'] == "os.environ['TELEGRAM_BOT_TOKEN']" else test_settings['TELEGRAM_BOT_TOKEN']
    TEST_YOUR_CHAT_ID = os.environ['YOUR_CHAT_ID'] if test_settings['YOUR_CHAT_ID'] == "os.environ['YOUR_CHAT_ID']" else test_settings['YOUR_CHAT_ID']
    TEST_TOPIC_ID = os.environ['TOPIC_ID'] if test_settings['TOPIC_ID'] == "os.environ['TOPIC_ID']" else test_settings['TOPIC_ID']
    TEST_TELEGRAM_API_ID = os.environ['TELEGRAM_API_ID'] if test_settings['TELEGRAM_API_ID'] == "os.environ['TELEGRAM_API_ID']" else test_settings['TELEGRAM_API_ID']
    TEST_TELEGRAM_API_HASH = os.environ['TELEGRAM_API_HASH'] if test_settings['TELEGRAM_API_HASH'] == "os.environ['TELEGRAM_API_HASH']" else test_settings['TELEGRAM_API_HASH']
    TEST_TELEGRAM_USERNAME = os.environ['TELEGRAM_USERNAME'] if test_settings['TELEGRAM_USERNAME'] == "os.environ['TELEGRAM_USERNAME']" else test_settings['TELEGRAM_USERNAME']
else:
    # If no test settings, use main settings
    TEST_TELEGRAM_BOT_TOKEN = TELEGRAM_BOT_TOKEN
    TEST_YOUR_CHAT_ID = YOUR_CHAT_ID
    TEST_TOPIC_ID = TOPIC_ID
    TEST_TELEGRAM_API_ID = TELEGRAM_API_ID
    TEST_TELEGRAM_API_HASH = TELEGRAM_API_HASH
    TEST_TELEGRAM_USERNAME = TELEGRAM_USERNAME

report_file = 'README.md'