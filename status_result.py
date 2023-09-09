import zipfile
import json
import hashlib


# Save the status of the script to a JSON file
def save_status(status_file, status, archive_filename):
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=4)
        print(f'{archive_filename}: Script status saved to', status_file)


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
        old_files = {item["name"]: item for item in old_dir if "name" in item}
        new_files = {item["name"]: item for item in new_dir if "name" in item}

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


def process_items(input_items):
    def parse(value, folder):
        for item in value:
            path_parts = item["name"].split('/')

            for part in path_parts[:-1]:
                if part not in folder:
                    folder[part] = {}
                folder = folder[part]

            folder_name = path_parts[-1]
            if "children" in item:
                folder[folder_name] = process_items(item["children"])
            else:
                file_name = folder_name
                folder[file_name] = file_name + " (" + item["checksum"] + ")" if "checksum" in item else file_name

        return folder

    final_folder = {}
    if isinstance(input_items, dict):
        for key, value in input_items.items():
            parse(value, final_folder)
    else:
        parse(input_items, final_folder)
    return final_folder
