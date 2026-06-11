import os
import json
import asyncio
from datetime import datetime
from pytz import timezone
import requests
import sys
from archives import process_archive
from settings import report_file, archives_output_dir, github_api_url
from report import create_html_report, send_to_tg
from settings import aio_zip_url
from files import download_extract_merge_json, download_file, remove_unlisted_directories
from archives import process_archives_from_json
from settings import file_to_extract, output_json_path
from archive_handler import handle_archive

# Додати функцію для отримання ID повідомлення з командного рядка або з середовища
def get_reply_message_id():
    # Спочатку перевіряємо аргументи командного рядка
    for arg in sys.argv[1:]:
        if arg not in ["--force", "-f"]:
            try:
                return int(arg)
            except ValueError:
                pass
    
    # Якщо немає в аргументах командного рядка, перевіряємо змінні середовища
    reply_id = os.environ.get('REPLY_MESSAGE_ID')
    if reply_id:
        try:
            return int(reply_id)
        except ValueError:
            pass
    
    return None

# Check latest GitHub release info (tag name and maximum assets update time)
def check_last_github_release_info():
    try:
        response = requests.get(github_api_url)
        if response.status_code == 200:
            release_data = response.json()
            tag_name = release_data.get('tag_name')
            
            # Find the maximum updated_at among all assets
            assets = release_data.get('assets', [])
            updated_dates = [asset.get('updated_at') for asset in assets if asset.get('updated_at')]
            
            if updated_dates:
                max_updated = max(updated_dates)
            else:
                max_updated = release_data.get('published_at') or release_data.get('created_at')
                
            return {
                "tag_name": tag_name,
                "assets_updated_at": max_updated
            }
        else:
            print('Error getting release info from GitHub API:', response.status_code)
            print('Response:', response.text)
            return None
    except Exception as e:
        print('Error checking GitHub release info:', e)
        return None

# Load and save the last check information
def load_last_check_info():
    try:
        if os.path.exists('last_check.json'):
            with open('last_check.json', 'r') as f:
                data = json.load(f)
                # Backward compatibility check
                if 'last_check_date' in data and 'tag_name' not in data:
                    return None
                return data
        return None
    except Exception as e:
        print('Error loading last check info:', e)
        return None

def save_last_check_info(info):
    try:
        with open('last_check.json', 'w') as f:
            json.dump(info, f)
    except Exception as e:
        print('Error saving last check info:', e)

async def main():
    # Check for force execution flag (--force or -f)
    force_mode = "--force" in sys.argv or "-f" in sys.argv
    
    # Get message ID for reply
    reply_message_id = get_reply_message_id()
    print(f"Got reply_message_id: {reply_message_id}")
    
    # Get latest release info
    last_release_info = check_last_github_release_info()
    if not last_release_info:
        print("Cannot get the latest release info. Exiting.")
        return
    
    # Get last check info
    last_check_info = load_last_check_info()
    
    # If last check info exists and matches current release info, exit (unless force)
    is_changed = True
    if not force_mode and last_check_info:
        same_tag = last_check_info.get('tag_name') == last_release_info.get('tag_name')
        same_assets = last_check_info.get('assets_updated_at') == last_release_info.get('assets_updated_at')
        if same_tag and same_assets:
            is_changed = False
            
    if not force_mode and not is_changed:
        print(f"No new releases or asset updates since last check (Tag: {last_release_info.get('tag_name')}, Assets: {last_release_info.get('assets_updated_at')}). Exiting.")
        return
    
    print(f"New release or asset changes detected!")
    print(f"Last release info: {last_release_info}")
    print(f"Previous check info: {last_check_info or 'None (first run)'}")
    
    # Продовжуємо за старим алгоритмом, якщо є новий реліз
    html_report_content = ''

    # Переконатися, що директорія для архівів існує
    if not os.path.exists(archives_output_dir):
        os.makedirs(archives_output_dir)

    custom_packs_path = download_extract_merge_json(aio_zip_url, file_to_extract, output_json_path)

    with open(custom_packs_path, 'r') as f:
        custom_packs_dict = json.load(f)

    archives = process_archives_from_json(custom_packs_dict)

    for archive in archives:
        url = archive["url"]
        filename = archive["filename"]
        filename_from_url = os.path.splitext(os.path.basename(url))[0]
        archive_output_dir = (filename + '_output')
        comparison_results_file = os.path.join(archive_output_dir, 'comparison_results.json')
        archive_name = os.path.join(archive_output_dir, filename_from_url)
        archive_name_for_tg = os.path.join(archive_output_dir, filename)
        status_file = os.path.join(archive_output_dir, 'status.json')
        archive_file = os.path.join(archive_name + '.zip')
        is_folder_exist = True if os.path.exists(archive_output_dir) else False
        changes = process_archive(archive)

        if changes:
            print(f"{archive['filename']}: Archive processed.")
            telegram = 1
            # Просто викликаємо handle_archive для контролю цілісності без модифікацій
            handle_archive(archive_file, filename, filename_from_url, 
                           output_folder=archives_output_dir)
        else:
            print(f"{archive['filename']}: No changes detected in the archive since the last execution.")
            telegram = 1 if force_mode else 0

        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status = json.load(f)

        if os.path.exists(comparison_results_file):
            with open(comparison_results_file, 'r') as f:
                comparison_results = json.load(f)

            last_modified = status["last_archive_modification"]

            if is_folder_exist:
                result = create_html_report(comparison_results, last_modified, archive["filename"])
            else:
                result = "<code>New archive was added.</code>"

            if telegram:
                if all(keyword not in archive_name for keyword in ["4BRICK", "AIO", "AIOB", "Refresh", "Placebo"]) and result:
                    try:
                        # Передаємо ID повідомлення для відповіді
                        await send_to_tg(result, archive_file, archive_name_for_tg, reply_message_id)
                        print("Report sent to Telegram as a reply to message ID:", reply_message_id)
                    except Exception as e:
                        print(f"Error sending report to Telegram: {e}")

            html_report_content += f'<h2>Archive Comparison Report for <b>{archive["filename"]}</b></h2>'
            html_report_content += result
            html_report_content += '<hr>\n\n'

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_report_content)

    print("All archives processed.")

    remove_unlisted_directories(custom_packs_dict, ".")
    
    # Save current release info as last checked info
    save_last_check_info(last_release_info)
    print(f"Updated last check info to {last_release_info}")

if __name__ == "__main__":
    # Використовуємо asyncio.run замість циклу подій вручну
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error in main function: {e}")