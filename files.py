import requests
import os
import shutil
import sys
from datetime import datetime

# Download a file from a URL
def download_file(url, output_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print('Archive downloaded successfully.')
    else:
        print('Error downloading archive:', response.status_code)

# Remove directories that are not present in custom_packs
def remove_unlisted_directories(custom_packs, output_parent_dir):
    pack_directories = [pack_name + '_output' for pack_name in custom_packs]

    for entry in os.listdir(output_parent_dir):
        entry_path = os.path.join(output_parent_dir, entry)
        if os.path.isdir(entry_path) and entry.endswith('_output') and entry not in pack_directories:
            shutil.rmtree(entry_path)
            print(f"Removed directory: {entry}")

# Get the last modified date of the file from the URL
def get_last_modified(url):
    try:
        head_response = requests.head(url)
        if head_response.status_code == 200:
            last_modified = (datetime.strptime(head_response.headers.get('Last-Modified'), '%a, %d %b %Y %H:%M:%S %Z')).isoformat()
            return last_modified
        else:
            print('Error getting Last-Modified:', head_response.status_code)
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        sys.exit(1)