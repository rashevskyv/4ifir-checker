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

aio_zip_url = ["https://sintez.io/AIO.zip", "https://sintez.io/AIOB.zip"]
# aio_zip_url = ["http://192.168.50.168/4ifir/AIO.zip", "http://192.168.50.168/4ifir/AIOB.zip"]
aio_zip_path = "aio.zip"
custom_packs_path = "custom_packs.json"
file_to_extract = "config/aio-switch-updater/custom_packs.json"
output_json_path = "custom_packs.json"

# Load the configuration from external file

settings = load_config('settings.json')
# settings = load_config('local_settings.json')
# settings = load_config('test_settings.json')

TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN'] if settings['TELEGRAM_BOT_TOKEN'] == "os.environ['TELEGRAM_BOT_TOKEN']" else settings['TELEGRAM_BOT_TOKEN']
YOUR_CHAT_ID = settings['YOUR_CHAT_ID']
TOPIC_ID = settings['TOPIC_ID']
TELEGRAM_API_ID = settings['TELEGRAM_API_ID']
TELEGRAM_API_HASH = settings['TELEGRAM_API_HASH']
TELEGRAM_USERNAME = settings['TELEGRAM_USERNAME']
report_file = 'README.md'