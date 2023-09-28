import os
import json
from datetime import datetime, timedelta
from pytz import timezone
from status_result import save_status, save_comparison_results, compare_checksums, build_tree_and_save_checksums
from files import get_last_modified, download_file

def process_archives_from_json(custom_packs_dict):
    archives = []
    for category, packs in custom_packs_dict.items():
        for pack_name, pack_url in packs.items():
            archives.append({"filename": pack_name, "url": pack_url})
    return archives

def process_archive(archive):
    url = archive["url"]
    filename = archive["filename"]
    output_dir = filename + '_output'
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    downld_file = os.path.join(output_dir, filename + '.zip')
    status_file = os.path.join(output_dir, 'status.json')
    old_checksum_file = os.path.join(output_dir, 'old_checksums.json')
    new_checksum_file = os.path.join(output_dir, 'new_checksums.json')
    comparison_results_file = os.path.join(output_dir, 'comparison_results.json')

    # Load the status file
    try:
        with open(status_file, 'r') as f:
            status = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"{archive['filename']}: No status file found, creating a new one.")
        status = {}

    # Check if the archive has been modified
    # Convert the current time to GMT+3 and then to ISO format
    def get_current_time_gmt3():
        current_time_utc = datetime.now(timezone('UTC'))
        current_time_gmt3 = current_time_utc.astimezone(timezone('Etc/GMT-3'))
        return current_time_gmt3.isoformat()

    last_modified = get_last_modified(url)
    status["last_execution"] =  get_current_time_gmt3()

    if os.path.exists(comparison_results_file):
            with open(comparison_results_file, 'r') as f:
                comparison_results = json.load(f)
    else: 
        comparison_results = {"added": [], "removed": [], "modified": []}

    if status.get("last_archive_modification") != last_modified:
        download_file(url, downld_file)
        
        # Build the tree structure and calculate checksums
        new_checksums = build_tree_and_save_checksums(downld_file)

        # Compare with the previous checksums if they exist
        if os.path.exists(old_checksum_file):
            with open(old_checksum_file, 'r') as f:
                old_checksums = json.load(f)
        else:
            old_checksums = {}
            with open(old_checksum_file, 'w') as f:
                json.dump(old_checksums, f)

        comparison_results = compare_checksums(old_checksums, new_checksums)

        # Save the comparison results to a file
        save_comparison_results(comparison_results, comparison_results_file)

        # Save the new checksums
        with open(new_checksum_file, 'w') as f:
            json.dump(new_checksums, f, indent=4)

        # Move the new checksums to the old checksums file
        os.replace(new_checksum_file, old_checksum_file)
    else:
        if not os.path.exists(downld_file):
            print(f"{downld_file}: No archive found, downloading a new one.")
            download_file(url, downld_file)
            if os.path.exists(downld_file):
                print(f"{downld_file}: Archive downloaded.")
            else:
                print(f"{downld_file}: Archive download failed.")
        return False
        
    status["last_archive_modification"] = last_modified
    save_status(status_file, status, filename)
    return True
