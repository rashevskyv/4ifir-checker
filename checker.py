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
    if len(sys.argv) > 1:
        try:
            return int(sys.argv[1])
        except (ValueError, IndexError):
            pass
    
    # Якщо немає в аргументах командного рядка, перевіряємо змінні середовища
    reply_id = os.environ.get('REPLY_MESSAGE_ID')
    if reply_id:
        try:
            return int(reply_id)
        except ValueError:
            pass
    
    return None

# Перевірка дати останнього релізу на GitHub
def check_last_github_release():
    try:
        # Отримати інформацію про останній реліз
        response = requests.get(github_api_url)
        if response.status_code == 200:
            release_data = response.json()
            # Отримати дату публікації останнього релізу
            published_at_utc = datetime.strptime(release_data['published_at'], '%Y-%m-%dT%H:%M:%SZ')
            # Перетворення в UTC часовий пояс
            published_at_utc = published_at_utc.replace(tzinfo=timezone('UTC'))
            # Перетворення в GMT+3
            published_at_gmt3 = published_at_utc.astimezone(timezone('Etc/GMT-3'))
            return published_at_gmt3.isoformat()
        else:
            print('Error getting release info from GitHub API:', response.status_code)
            print('Response:', response.text)
            return None
    except Exception as e:
        print('Error checking GitHub release date:', e)
        return None

# Завантаження і збереження дати останньої перевірки
def load_last_check_date():
    try:
        if os.path.exists('last_check.json'):
            with open('last_check.json', 'r') as f:
                data = json.load(f)
                return data.get('last_check_date')
        return None
    except Exception as e:
        print('Error loading last check date:', e)
        return None

def save_last_check_date(date_str):
    try:
        with open('last_check.json', 'w') as f:
            json.dump({'last_check_date': date_str}, f)
    except Exception as e:
        print('Error saving last check date:', e)

async def main():
    # Отримати ID повідомлення для відповіді
    reply_message_id = get_reply_message_id()
    print(f"Got reply_message_id: {reply_message_id}")
    
    # Отримати дату останнього релізу
    last_release_date = check_last_github_release()
    if not last_release_date:
        print("Cannot get the latest release date. Exiting.")
        return
    
    # Отримати дату останньої перевірки
    last_check_date = load_last_check_date()
    
    # Якщо дата останньої перевірки існує і дорівнює даті останнього релізу,
    # завершити роботу скрипта
    if last_check_date and last_check_date == last_release_date:
        print(f"No new releases since last check (Last release: {last_release_date}). Exiting.")
        return
    
    print(f"New release detected! Last release date: {last_release_date}")
    print(f"Previous check date: {last_check_date or 'None (first run)'}")
    
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
            telegram = 0

        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status = json.load(f)

        if os.path.exists(comparison_results_file):
            with open(comparison_results_file, 'r') as f:
                comparison_results = json.load(f)

            last_modified = status["last_archive_modification"]

            if is_folder_exist:
                result = create_html_report(comparison_results, last_modified)
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
    
    # Зберегти поточну дату релізу як дату останньої перевірки
    save_last_check_date(last_release_date)
    print(f"Updated last check date to {last_release_date}")

if __name__ == "__main__":
    # Використовуємо asyncio.run замість циклу подій вручну
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error in main function: {e}")