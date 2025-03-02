import requests
import os
import shutil
import sys
from datetime import datetime, timedelta
from pytz import timezone
from report import send_tg_message
import asyncio
import json
import zipfile
from settings import output_json_path, github_api_url

# Download a file from a URL
def download_file(url, output_path):
    print(f"Downloading {url}")
    try: 
        response = requests.get(url)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f'{output_path}: Archive downloaded successfully.')
        with open("serverresponse.txt", 'r') as server_response:
            if server_response.read() == '0':
                asyncio.run(send_tg_message("Server is up!"))
                with open("serverresponse.txt", 'w') as server_response:
                        server_response.write('1')
    except Exception as e:
        print(f'Error downloading archive. {e}')
        with open("serverresponse.txt", 'r') as server_response:
            if server_response.read() == '1':
                asyncio.run(send_tg_message("""<b>Server is down</b>                                            
                                            
Нагадую, що в репозиторії чекера на гітхаб лежать версії зі зміненим джерелом оновлень. То ж коли і якщо в вас не працює аіо, або сервер Кулера лежить, використовуйте ці версії. Ще раз - нічого не змінено, окрім сервера оновлень. Версії відповідні версіям з пульса https://github.com/rashevskyv/4ifir-checker/tree/main/github

Reminder: versions with a changed update source are available in the checker repository on GitHub. So if AIO doesn't work for you or Cooler's server is down, use thise versions. Once again - nothing has been changed except the update server. The versions correspond to those from Pulse https://github.com/rashevskyv/4ifir-checker/tree/main/github

Напоминаю, что в репозитории чекера на гитхаб лежат версии с измененным источником обновлений. Так что если у вас не работает аио, или сервер Кулера лежит, используйте эти версии. Еще раз - ничего не изменено, кроме сервера обновлений. Версии соответствуют версиям с пульса https://github.com/rashevskyv/4ifir-checker/tree/main/github"""))
                with open("serverresponse.txt", 'w') as server_response:
                    server_response.write('0')
        sys.exit(0)

# Remove directories that are not present in custom_packs
def remove_unlisted_directories(custom_packs_dict, output_parent_dir):

    archives = []
    for category, packs in custom_packs_dict.items():
        for pack_name, pack_url in packs.items():
            archives.append({"filename": pack_name})

    pack_directories = [archive["filename"] + '_output' for archive in archives]

    for entry in os.listdir(output_parent_dir):
        entry_path = os.path.join(output_parent_dir, entry)
        if os.path.isdir(entry_path) and entry.endswith('_output') and entry not in pack_directories:
            shutil.rmtree(entry_path)
            print(f"Removed directory: {entry}")

    if os.path.exists(output_json_path):
        os.remove(output_json_path)
        print(f"Removed file: {output_json_path}")

# Updated function to get the last modified date from the GitHub API
def get_last_modified(url):
    try:
        # Instead of checking the URL's last-modified header,
        # we'll get the latest release date from GitHub API
        response = requests.get(github_api_url)
        if response.status_code == 200:
            release_data = response.json()
            # Get the published_at date of the latest release
            published_at_utc = datetime.strptime(release_data['published_at'], '%Y-%m-%dT%H:%M:%SZ')
            # Convert to UTC timezone
            published_at_utc = published_at_utc.replace(tzinfo=timezone('UTC'))
            # Convert to GMT+3
            published_at_gmt3 = published_at_utc.astimezone(timezone('Etc/GMT-3'))
            return published_at_gmt3.isoformat()
        else:
            print('Error getting release info from GitHub API:', response.status_code)
            print('Response:', response.text)
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        sys.exit(1)
    except KeyError as e:
        print('Error parsing GitHub API response:', e)
        print('Response content:', response.text)
        sys.exit(1)

def extract_file_from_zip(zip_path, file_to_extract, output_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        try:
            with zip_ref.open(file_to_extract, 'r') as file:
                with open(output_path, 'wb') as output_file:
                    output_file.write(file.read())
        except KeyError:
            print(f"Error: {file_to_extract} not found in {zip_path}")
            sys.exit(1)

def download_extract_merge_json(aio_zip_urls, file_to_extract, output_json_path):
    temp_dirs = []
    temp_json_files = []

    # Шлях до тимчасової папки
    temp_folder = 'temp'

    # Перевірка наявності папки, якщо існує - видалення
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)

    # Створення тимчасової папки
    os.makedirs(temp_folder)

    # Скачування та розпакування файлів
    for url in aio_zip_urls:
        zip_name = os.path.basename(url)
        zip_path = os.path.join(temp_folder, zip_name)
        download_file(url, zip_path)
        output_path = os.path.join(temp_folder, zip_name + "_output")
        os.makedirs(output_path, exist_ok=True)
        temp_dirs.append(output_path)
        json_path = os.path.join(output_path, 'custom_packsB.json')
        extract_file_from_zip(zip_path, file_to_extract, json_path)
        temp_json_files.append(json_path)

    # Об'єднання JSON файлів (змінений порядок)
    merged_data = {}
    for json_file in temp_json_files:
        with open(json_file, 'r') as file:
            data = json.load(file)
        for category, packs in data.items():
            if category not in merged_data:
                merged_data[category] = packs
            else:
                for pack_name, pack_url in packs.items():
                    if pack_url not in merged_data[category].values():
                        merged_data[category][pack_name] = pack_url

    # Збереження об'єднаного JSON
    with open(output_json_path, 'w') as file:
        json.dump(merged_data, file, indent=4)

    # Видалення тимчасових файлів та директорії "temp"
    shutil.rmtree(temp_folder)

    return output_json_path