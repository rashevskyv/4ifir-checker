import requests
import os
import shutil
import sys
from datetime import datetime
from report import send_tg_message
import asyncio

# Download a file from a URL
def download_file(url, output_path):
    try: 
        response = requests.get(url)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print('Archive downloaded successfully.')
        with open("serverresponse.txt", 'r') as server_response:
            if server_response.read() == '0':
                asyncio.run(send_tg_message("Server is up!"))
                with open("serverresponse.txt", 'w') as server_response:
                        server_response.write('1')
    except:
        print('Error downloading archive.')
        with open("serverresponse.txt", 'r') as server_response:
            if server_response.read() == '1':
                asyncio.run(send_tg_message("Server is down"))
                with open("serverresponse.txt", 'w') as server_response:
                    server_response.write('0')
        sys.exit(0)

# Remove directories that are not present in custom_packs
def remove_unlisted_directories(custom_packs_dict, output_parent_dir):

    archives = []
    for category, packs in custom_packs_dict.items():
        for pack_name, pack_url in packs.items():
            archives.append({"url": pack_url})

    pack_directories = [os.path.splitext(os.path.basename(archive["url"]))[0] + '_output' for archive in archives]

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