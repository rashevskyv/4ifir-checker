import os
import json
from datetime import datetime
import zipfile
import sys
from files import download_file, get_last_modified
from settings import custom_packs_path, aio_zip_url, aio_zip_path, file_to_extract
from status_result import save_status, save_comparison_results, compare_checksums, build_tree_and_save_checksums

def extract_file_from_zip(zip_path, file_to_extract, output_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        try:
            with zip_ref.open(file_to_extract, 'r') as file:
                with open(output_path, 'wb') as output_file:
                    output_file.write(file.read())
        except KeyError:
            print(f"Error: {file_to_extract} not found in {zip_path}")
            sys.exit(1)

def process_archives():
    archives = []
    for category, packs in custom_packs_dict.items():
        for pack_name, pack_url in packs.items():
            archives.append({"filename": pack_name, "url": pack_url})
    return archives

download_file(aio_zip_url, aio_zip_path)
extract_file_from_zip(aio_zip_path, file_to_extract, custom_packs_path)

with open(custom_packs_path, 'r') as f:
	custom_packs_dict = json.load(f)

archives = process_archives()

def process_archive(archive):
    url = archive["url"]
    filename = archive["filename"]
    output_dir = filename+'_output'
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
        print('No status file found, creating a new one.')
        status = {}

    # Check if the archive has been modified
    last_modified = get_last_modified(url)
    status["last_execution"] = datetime.now().isoformat()

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

            comparison_results = compare_checksums(old_checksums, new_checksums)

            # Save the comparison results to a file
            save_comparison_results(comparison_results, comparison_results_file)

        # Save the new checksums
        with open(new_checksum_file, 'w') as f:
            json.dump(new_checksums, f, indent=4)

        # Move the new checksums to the old checksums file
        os.replace(new_checksum_file, old_checksum_file)
    else:
        return False
        
    status["last_archive_modification"] = last_modified
    save_status(status_file, status, filename)
    return True
