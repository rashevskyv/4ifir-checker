import os
import requests
import hashlib
import json
from datetime import datetime, timedelta
import zipfile
import sys

# Get last modified date of the file from URL
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

# Save comparison results to a JSON file
def save_comparison_results(results, output_file):
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)

# Create Markdown report with the comparison results
def create_md_report(results, output_file, execution_date, last_modified):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('# Archive Comparison Report\n\n')

        f.write(f'**Last script execution date:** {execution_date}\n\n')
        f.write(f'**Last archive modification date:** {last_modified}\n\n')

        def process_item(item, level=1):
            prefix = '  ' * level
            if item["type"] == "directory":
                return f"{prefix}- **{item['name']}/:**\n" + ''.join(process_item(child, level + 1) for child in item["children"])
            else:
                return f"{prefix}- {item['name']} ({item['checksum']})\n"

        for change_type, items in results.items():
            if change_type == "added":
                f.write('## Added files/folders\n\n')
            elif change_type == "removed":
                f.write('## Removed files/folders\n\n')
            elif change_type == "modified":
                f.write('## Modified files\n\n')

            if items:
                for item in items:
                    f.write(process_item(item))
            else:
                f.write('No changes\n')
            f.write('\n')

# Variables
# url = 'http://127.0.0.1/4IFIR.zip'
url = 'https://sintez.io/4IFIR.zip'
filename = '4IFIR.zip'
output_dir = ''
downld_file = os.path.join(output_dir, filename)
status_file = os.path.join(output_dir, 'status.json')
old_checksum_file = os.path.join(output_dir, 'old_checksums.json')
new_checksum_file = os.path.join(output_dir, 'new_checksums.json')

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

        # Create Markdown report
        report_file = os.path.join(output_dir, 'README.md')
        create_md_report(comparison_results, report_file, status.get("last_execution"), last_modified)

    # Save the new checksums
    with open(new_checksum_file, 'w') as f:
        json.dump(new_checksums, f, indent=4)

    # Move the new checksums to the old checksums file
    os.replace(new_checksum_file, old_checksum_file)
else:
    print("No changes detected in the archive since the last execution.")

# Update the status file
status["last_execution"] = datetime.now().isoformat()
status["last_archive_modification"] = last_modified
save_status(status_file, status)

print("Script finished.")