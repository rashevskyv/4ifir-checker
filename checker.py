import os
import requests
import hashlib
import json
from datetime import datetime, timedelta
import zipfile
import sys

def create_directories():
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    if not os.path.isdir(downld_dir):
        os.makedirs(downld_dir)


def get_last_modified(url):
    try:
        head_response = requests.head(url)
        if head_response.status_code == 200:
            last_modified = (datetime.strptime(head_response.headers.get('Last-Modified'), '%a, %d %b %Y %H:%M:%S %Z') + timedelta(hours=2)).isoformat()
            return last_modified
        else:
            print('Error getting Last-Modified:', head_response.status_code)
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        sys.exit(1)

def download_file(url, output_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print('Archive downloaded successfully.')
    else:
        print('Error downloading archive:', response.status_code)

def save_status(status_file, status):
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=4)
        print('Script status saved to', status_file)

def build_tree(path, contents):
    parts = path.split('/', 1)
    current = parts[0]
    
    if len(parts) == 1:
        contents.append({"type": "file", "name": current})
    else:
        directory_found = False
        for item in contents:
            if item["type"] == "directory" and item["name"] == current:
                directory_found = True
                build_tree(parts[1], item["children"])
                break
        
        if not directory_found:
            new_dir = {"type": "directory", "name": current, "children": []}
            build_tree(parts[1], new_dir["children"])
            contents.append(new_dir)

def build_tree_and_save_checksums(downld_file):
    with zipfile.ZipFile(downld_file, 'r') as zip_ref:
        file_names = zip_ref.namelist()
        archive_contents = []

        for file_name in file_names:
            if not file_name.endswith('/'):  # Пропустить папки
                with zip_ref.open(file_name, 'r') as file:
                    file_content = file.read()
                    checksum = hashlib.md5(file_content).hexdigest()

                    build_tree(file_name, archive_contents)

                    # Ищем файл в древовидной структуре и добавляем чексумму
                    current = archive_contents
                    for part in file_name.split('/'):
                        for item in current:
                            if item["name"] == part:
                                if item["type"] == "file":
                                    item["checksum"] = checksum
                                else:
                                    current = item["children"]
                                break
    return archive_contents

def compare_checksums(old_checksums, new_checksums):
    result = {"added": [], "removed": [], "modified": []}

    def compare_directories(old_dir, new_dir):
        old_files = {item["name"]: item for item in old_dir}
        new_files = {item["name"]: item for item in new_dir}

        for name, new_item in new_files.items():
            if name not in old_files:
                result["added"].append(new_item)
            else:
                old_item = old_files[name]
                if new_item["type"] == "file" and old_item["type"] == "file":
                    if new_item["checksum"] != old_item["checksum"]:
                        result["modified"].append(new_item)
                elif new_item["type"] == "directory" and old_item["type"] == "directory":
                    compare_directories(old_item["children"], new_item["children"])

        for name, old_item in old_files.items():
            if name not in new_files:
                result["removed"].append(old_item)

    compare_directories(old_checksums, new_checksums)
    return result

def save_comparison_results(results, output_file):
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)


def delete_folder(folder_to_delete):
    # Удаляем все файлы и подпапки
    if os.path.exists(folder_to_delete):
        for root, dirs, files in os.walk(folder_to_delete, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(folder_to_delete)
        print(f"Папка '{folder_to_delete}' и ее содержимое были успешно удалены.")
    else:
        print(f"Папка '{folder_to_delete}' не найдена.")
    # Удаляем саму папку

def create_md_report(results, output_file, execution_date, last_modified):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('# Отчет о сравнении архивов\n\n')

        f.write(f'**Дата последнего запуска программы:** {execution_date}\n\n')
        f.write(f'**Дата изменения архива:** {last_modified}\n\n')

        def process_item(item, level=1):
            prefix = '  ' * level
            if item["type"] == "directory":
                return f"{prefix}- **{item['name']}/:**\n" + ''.join(process_item(child, level + 1) for child in item["children"])
            else:
                return f"{prefix}- {item['name']} ({item['checksum']})\n"

        for change_type, items in results.items():
            if change_type == "added":
                f.write('## Добавленные файлы/папки\n\n')
            elif change_type == "removed":
                f.write('## Удаленные файлы/папки\n\n')
            elif change_type == "modified":
                f.write('## Измененные файлы\n\n')

            if items:
                for item in items:
                    f.write(process_item(item))
            else:
                f.write('Нет изменений\n')
            f.write('\n')


# Variables
url = 'https://sintez.io/4IFIR.zip'
filename = '4IFIR.zip'
output_dir = 'F:\\git\\4efir_checker'
downld_dir = os.path.join(output_dir, 'download')
downld_file = os.path.join(downld_dir, filename)
status_file = os.path.join(output_dir, 'status.json')
folder_new = os.path.join(output_dir, 'new')
folder_old = os.path.join(output_dir, 'old')

# Load the status file
try:
    with open(status_file, 'r') as f:
        status = json.load(f)
except (json.JSONDecodeError, FileNotFoundError) as e:
    print('Error loading status file:', e)
    status = {}

# Get last modified date
last_modified = get_last_modified(url)
print('Last-Modified :', last_modified)
print('execution_date:', status['execution_date'])

# Create directories if not exists
create_directories()

# Download the file if not up to date
if os.path.isfile(downld_file) and last_modified < status['execution_date']:
    print('Archive already downloaded and is up to date.')
else:
    download_file(url, downld_file)


    if os.path.exists(folder_new):
        if os.path.exists(folder_old):
            delete_folder(folder_old)
        os.rename(folder_new, folder_old)
    if not os.path.isdir(folder_new):
        os.makedirs(folder_new)


    # Build tree and save checksums
    checksum_file = os.path.join(folder_new, 'checksums.json')

    archive_contents = build_tree_and_save_checksums(downld_file)
    with open(checksum_file, 'w') as json_file:
        json.dump(archive_contents, json_file, indent=4)

old_checksum_file = os.path.join(folder_old, 'checksums.json')
new_checksum_file = os.path.join(folder_new, 'checksums.json')

if os.path.exists(old_checksum_file) and os.path.exists(new_checksum_file):
    with open(old_checksum_file, 'r') as f:
        old_checksums = json.load(f)

    with open(new_checksum_file, 'r') as f:
        new_checksums = json.load(f)

    comparison_results = compare_checksums(old_checksums, new_checksums)
    comparison_file = os.path.join(output_dir, 'comparison.json')
    save_comparison_results(comparison_results, comparison_file)

    md_report_file = os.path.join(output_dir, 'README.md')
    create_md_report(comparison_results, md_report_file, status['execution_date'], status['last_modified'])

# Save the status of the script to a JSON file
status = {'last_modified': last_modified, 'execution_date': datetime.now().isoformat()}
save_status(status_file, status)