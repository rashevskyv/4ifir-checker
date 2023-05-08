import os
import json
import asyncio
from aiogram.types import InputFile
from archives import process_archive, custom_packs_dict, archives
from settings import TELEGRAM_BOT_TOKEN, YOUR_CHAT_ID, TOPIC_ID, report_file
from report import create_html_report, send_telegram_message
from files import remove_unlisted_directories

def main():
    html_report_content = ''

    for archive in archives:
        if (process_archive(archive)):
            print(f"Archive {archive['filename']} processed.")
            telegram = 1
        else:
            print("No changes detected in the archive since the last execution.")
            telegram = 0

        archive_output_dir = os.path.join(archive["filename"] + '_output')
        comparison_results_file = os.path.join(archive_output_dir, 'comparison_results.json')
        status_file = os.path.join(archive_output_dir, 'status.json')
        archive_file = os.path.join(archive_output_dir, archive["filename"] + '.zip')

        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status = json.load(f)

        if os.path.exists(comparison_results_file):
            with open(comparison_results_file, 'r') as f:
                comparison_results = json.load(f)

            last_modified = status["last_archive_modification"]
            result = create_html_report(comparison_results, last_modified, archive["filename"])

            if (telegram):
                with open(archive_file, 'rb') as file:
                    input_file = InputFile(file)
                    asyncio.run(send_telegram_message(TELEGRAM_BOT_TOKEN, YOUR_CHAT_ID, TOPIC_ID, result, input_file))
                    print("Report sent to Telegram.")

            html_report_content += result
            html_report_content += '<hr>\n\n'

    # Write the report to a README.md file
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_report_content)

    print("All archives processed.")

    custom_pack_names = []
    for category, packs in custom_packs_dict.items():
        for pack_name, _ in packs.items():
            custom_pack_names.append(pack_name)

    remove_unlisted_directories(custom_pack_names, ".")

if __name__ == "__main__":
    main()