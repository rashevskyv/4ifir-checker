import os
import json
import asyncio
from archives import process_archive
from settings import report_file
from report import create_html_report, send_to_tg
from settings import aio_zip_url
from files import download_extract_merge_json, download_file, remove_unlisted_directories
from archives import process_archives_from_json
from settings import file_to_extract, output_json_path, report_file
from archive_handler import handle_archive

async def main():  # Додаємо async до функції main
    html_report_content = ''

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

        if (changes):
            print(f"{archive['filename']}: Archive processed.")
            telegram = 1
            handle_archive(archive_file, filename, filename_from_url)
        else:
            print(f"{archive['filename']}: No changes detected in the archive since the last execution.")
            telegram = 0
            github_file = os.path.join('github', filename_from_url + '.zip')
            if not os.path.exists(github_file):
                handle_archive(archive_file, filename, filename_from_url)

        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status = json.load(f)

        if os.path.exists(comparison_results_file):
            with open(comparison_results_file, 'r') as f:
                comparison_results = json.load(f)

            last_modified = status["last_archive_modification"]

            if (is_folder_exist):
                result = create_html_report(comparison_results, last_modified)
            else:
                result = "<code>New archive was added.</code>"

            if telegram:
                if all(keyword not in archive_name for keyword in ["4BRICK", "AIO", "AIOB", "Refresh", "Placebo"]) and result:
                    await send_to_tg(result, archive_file, archive_name_for_tg)  # Використовуємо await
                    print("Report sent to Telegram.")

            html_report_content += f'<h2>Archive Comparison Report for <b>{archive["filename"]}</b></h2>'
            html_report_content += result
            html_report_content += '<hr>\n\n'

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_report_content)

    print("All archives processed.")

    remove_unlisted_directories(custom_packs_dict, ".")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())  # Запускаємо асинхронну функцію
    finally:
        loop.close()  # Закриваємо цикл подій після завершення