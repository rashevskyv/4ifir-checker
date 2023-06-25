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

aio_zip_url = "https://github.com/rashevskyv/4IFIR/releases/latest/download/AIO.zip"
# aio_zip_url = "http://127.0.0.1/aio.zip"
aio_zip_path = "aio.zip"
custom_packs_path = "custom_packs.json"
file_to_extract = "config/aio-switch-updater/custom_packs.json"

# Load the configuration from external file

settings = load_config('settings.json')
# settings = load_config('local_settings.json')
# settings = load_config('test_settings.json')

TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN'] if settings['TELEGRAM_BOT_TOKEN'] == "os.environ['TELEGRAM_BOT_TOKEN']" else settings['TELEGRAM_BOT_TOKEN']
YOUR_CHAT_ID = settings['YOUR_CHAT_ID']
TOPIC_ID = settings['TOPIC_ID']
report_file = 'README.md'