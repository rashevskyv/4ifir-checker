import os
import json
import asyncio
from archives import process_archive
from settings import report_file
from report import create_html_report, send_to_tg
from files import remove_unlisted_directories
from settings import aio_zip_url
from files import download_extract_merge_json
from archives import process_archives
from settings import file_to_extract, output_json_path

def main():
    html_report_content = ''

    custom_packs_path = download_extract_merge_json(aio_zip_url, file_to_extract, output_json_path)

    with open(custom_packs_path, 'r') as f:
        custom_packs_dict = json.load(f)

    archives = process_archives(custom_packs_dict)

    for archive in archives:
        if (process_archive(archive)):
            print(f"{archive['filename']}: Archive processed.")
            telegram = 1
        else:
            print(f"{archive['filename']}: No changes detected in the archive since the last execution.")
            telegram = 0

        filename = os.path.splitext(os.path.basename(archive["url"]))[0]
        archive_output_dir = (filename + '_output')
        comparison_results_file = os.path.join(archive_output_dir, 'comparison_results.json')
        archivename = os.path.join(archive_output_dir, archive["filename"])
        status_file = os.path.join(archive_output_dir, 'status.json')
        archive_file = os.path.join(archive_output_dir, filename + '.zip')

        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status = json.load(f)

        if os.path.exists(comparison_results_file):
            with open(comparison_results_file, 'r') as f:
                comparison_results = json.load(f)

            last_modified = status["last_archive_modification"]
            result = create_html_report(comparison_results, last_modified, archive["filename"])

            if (telegram):
                if "4BRICK" not in archivename:
                    asyncio.run(send_to_tg(result, archive_file, archivename))
                    print("Report sent to Telegram.")

            html_report_content += result
            html_report_content += '<hr>\n\n'

    # Write the report to a README.md file
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_report_content)

    print("All archives processed.")

    remove_unlisted_directories(custom_packs_dict, ".")

if __name__ == "__main__":
    main()