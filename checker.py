import os
import requests
import hashlib
import json
from datetime import datetime, timedelta
import zipfile
import sys
from telegram import Bot
from aiogram import Bot, types
import asyncio

# Get last modified date of the file from URL
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

# Download file from URL
def download_file(url, output_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print('Archive downloaded successfully.')
    else:
        print('Error downloading archive:', response.status_code)

# Save the status of the script to a JSON file
def save_status(status_file, status):
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=4)
        print('Script status saved to', status_file)

# Build tree structure and add the item to the tree
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

# Build tree structure, calculate checksums and save them
def build_tree_and_save_checksums(downld_file):
    with zipfile.ZipFile(downld_file, 'r') as zip_ref:
        file_names = zip_ref.namelist()
        archive_contents = []

        for file_name in file_names:
            if not file_name.endswith('/'):  # Skip directories
                with zip_ref.open(file_name, 'r') as file:
                    file_content = file.read()
                    checksum = hashlib.md5(file_content).hexdigest()

                    build_tree(file_name, archive_contents)

                    # Search for the file in the tree structure and add the checksum
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

# Compare checksums between old and new files
def compare_checksums(old_checksums, new_checksums):
    result = {"added": [], "removed": [], "modified": []}

    def compare_directories(old_dir, new_dir, path=""):
        old_files = {item["name"]: item for item in old_dir}
        new_files = {item["name"]: item for item in new_dir}

        for name, new_item in new_files.items():
            if name not in old_files:
                new_item_copy = new_item.copy()
                new_item_copy["name"] = f"{path}/{name}" if path else name
                result["added"].append(new_item_copy)
            else:
                old_item = old_files[name]
                if new_item["type"] == "file" and old_item["type"] == "file":
                    if new_item["checksum"] != old_item["checksum"]:
                        new_item_copy = new_item.copy()
                        new_item_copy["name"] = f"{path}/{name}" if path else name
                        result["modified"].append(new_item_copy)
                elif new_item["type"] == "directory" and old_item["type"] == "directory":
                    child_path = f"{path}/{name}" if path else name
                    compare_directories(old_item["children"], new_item["children"], child_path)

        for name, old_item in old_files.items():
            if name not in new_files:
                old_item_copy = old_item.copy()
                old_item_copy["name"] = f"{path}/{name}" if path else name
                result["removed"].append(old_item_copy)

    compare_directories(old_checksums, new_checksums)
    return result

# Save comparison results to a JSON file
def save_comparison_results(results, output_file):
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)

def process_items(items, indent_level=1):
    folder_tree = {}
    prefix = '  ' * indent_level

    for item in items:
        path_parts = item["name"].split('/')
        folder = folder_tree

        for part in path_parts[:-1]:
            if part not in folder:
                folder[part] = {}
            folder = folder[part]

        folder[path_parts[-1]] = item

    return folder_tree

def create_html_report(results, last_modified):
    report_content = ''
    report_content += '<h2>Archive Comparison Report</h2>'

    # formatted_execution_date = datetime.fromisoformat(execution_date).strftime('%d.%m.%Y %H:%M')
    formatted_last_modified = datetime.fromisoformat(last_modified).strftime('%d.%m.%Y %H:%M')
    # report_content += f'<b>Last script execution date:</b> {formatted_execution_date}<br>'
    report_content += f'<b>Last archive modification date:</b> {formatted_last_modified}<hr>\n\n'

    def render_tree(tree, level=1, last_child=False):
        tree_str = ""
        prefix = '  ' * (level - 1)

        if level > 1:
            prefix = '│ ' * (level - 2)
            if last_child:
                prefix += '└─'
            else:
                prefix += '├─'

        for index, (key, value) in enumerate(tree.items()):
            is_last_child = index == len(tree) - 1

            if isinstance(value, dict):
                if "name" in value and "checksum" in value:
                    file_name, file_extension = os.path.splitext(os.path.basename(value['name']))
                    tree_str += f"{prefix}{file_name}{file_extension} ({value['checksum']})\n"
                else:
                    tree_str += f"{prefix}{key}\n"
                    tree_str += render_tree(value, level + 1, is_last_child)

        return tree_str

    for change_type, items in results.items():
        if items:  # Add this condition
            if change_type == "added":
                report_content += '<h3>Added files/folders</h3>\n<code>'
            elif change_type == "removed":
                report_content += '<h3>Removed files/folders</h3>\n<code>'
            elif change_type == "modified":
                report_content += '<h3>Modified files</h3>\n<code>'

            folder_tree = process_items(items)
            report_content += render_tree(folder_tree)
            report_content += '</code>\n'  # Закрытие блока кода с помощью ```
    return report_content

def split_html_content(content, max_length=4096, tag='<code>'):
    content_length = len(content)
    if content_length <= max_length:
        return [content]

    blocks = []
    start_index = 0

    while start_index < content_length:
        end_index = start_index + max_length
        if end_index < content_length:
            end_index = content.rfind(tag, start_index, end_index)
            if end_index == -1:
                end_index = start_index + max_length

        blocks.append(content[start_index:end_index])
        start_index = end_index

    return blocks

async def send_telegram_message(bot_token, chat_id, message_thread_id, report_content):
    # Generate the list of changes
    report_content = report_content.replace("<h2>", "<b>").replace("</h2>", "</b>\n").replace("<h3>", "<b>").replace("</h3>", "</b>\n").replace("<br>", "\n").replace("<hr>", "\n-------------------------------")

    blocks = split_html_content(report_content)

    bot = Bot(token=bot_token)
    for part in blocks:
        await bot.send_message(chat_id=chat_id, text=part, parse_mode=types.ParseMode.HTML)
    await bot.close()

# Variables
# url = 'http://127.0.0.1/4IFIR.zip'
url = 'https://sintez.io/4IFIR.zip'
filename = '4IFIR.zip'
output_dir = ''
downld_file = os.path.join(output_dir, filename)
status_file = os.path.join(output_dir, 'status.json')
old_checksum_file = os.path.join(output_dir, 'old_checksums.json')
new_checksum_file = os.path.join(output_dir, 'new_checksums.json')
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
YOUR_CHAT_ID = '-1001277664260'
TOPIC_ID='98339'
# TOPIC_ID=''
modified=0

# Load the status file
try:
    with open(status_file, 'r') as f:
        status = json.load(f)
except (json.JSONDecodeError, FileNotFoundError) as e:
    print('No status file found, creating a new one.')
    status = {
        "last_execution": None,
        "last_archive_modification": None,
    }

# Check if the archive has been modified
last_modified = get_last_modified(url)

if os.path.exists(os.path.join(output_dir, 'comparison_results.json')):
        with open(os.path.join(output_dir, 'comparison_results.json'), 'r') as f:
            comparison_results = json.load(f)
else: 
    comparison_results = {"added": [], "removed": [], "modified": []}

if status.get("last_archive_modification") != last_modified:
    # Download the archive
    download_file(url, downld_file)

    # Build the tree structure and calculate checksums
    new_checksums = build_tree_and_save_checksums(downld_file)

    # Compare with the previous checksums if they exist
    if os.path.exists(old_checksum_file):
        with open(old_checksum_file, 'r') as f:
            old_checksums = json.load(f)

        comparison_results = compare_checksums(old_checksums, new_checksums)

        # Save the comparison results to a file
        result_file = os.path.join(output_dir, 'comparison_results.json')
        save_comparison_results(comparison_results, result_file)

    # Save the new checksums
    with open(new_checksum_file, 'w') as f:
        json.dump(new_checksums, f, indent=4)

    # Move the new checksums to the old checksums file
    os.replace(new_checksum_file, old_checksum_file)

    modified=1
else:
    print("No changes detected in the archive since the last execution.")

# status["last_execution"] = datetime.now().isoformat()
status["last_archive_modification"] = last_modified
save_status(status_file, status)

# Create Markdown report
report_file = os.path.join(output_dir, 'README.md')
html_report_content = create_html_report(comparison_results, last_modified)

# Записываем содержимое отчета в файл README.md
with open(report_file, 'w', encoding='utf-8') as f:
    f.write(html_report_content)

# Если есть изменения, отправляем содержимое отчета в Telegram
if (modified):
    asyncio.run(send_telegram_message(TELEGRAM_BOT_TOKEN, YOUR_CHAT_ID, TOPIC_ID, html_report_content))
    print("Report sent to Telegram.")
else:
    print("No changes to report.")

print("Script finished.")