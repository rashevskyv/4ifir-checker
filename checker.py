import os
import json
import asyncio
from archives import process_archive
from settings import report_file, archives_output_dir
from report import create_html_report, send_to_tg
from settings import aio_zip_url
from files import download_extract_merge_json, download_file, remove_unlisted_directories
from archives import process_archives_from_json
from settings import file_to_extract, output_json_path
from archive_handler import handle_archive

async def main():
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
                        await send_to_tg(result, archive_file, archive_name_for_tg)
                        print("Report sent to Telegram.")
                    except Exception as e:
                        print(f"Error sending report to Telegram: {e}")

            html_report_content += f'<h2>Archive Comparison Report for <b>{archive["filename"]}</b></h2>'
            html_report_content += result
            html_report_content += '<hr>\n\n'

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_report_content)

    print("All archives processed.")

    remove_unlisted_directories(custom_packs_dict, ".")

if __name__ == "__main__":
    # Використовуємо asyncio.run замість циклу подій вручну
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error in main function: {e}")