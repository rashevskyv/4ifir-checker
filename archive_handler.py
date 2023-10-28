import os
import json
import shutil

def handle_archive(archive_path, local_filename, github_filename, temp_folder='github/temp', output_folder='github'):
    archive_name = os.path.basename(archive_path)
    new_archive_path = os.path.join(output_folder, archive_name)
    sintez_link = 'sintez.io/'
    github_link = 'github.com/rashevskyv/4ifir-checker/raw/main/github/'
    custom_packs_path = 'config/aio-switch-updater/custom_packs.json'
    custom_packs_temp_path = os.path.join(temp_folder, custom_packs_path)

    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)

    def modify_json_data(data, sintez_link, github_link, local_filename, github_filename):
        # Iterate through each key-value pair in the dictionary
        for key, value in data.items():
            if isinstance(value, dict):
                # Recursive call for nested dictionaries
                modify_json_data(value, sintez_link, github_link, local_filename, github_filename)
            else:
                # Replace the URLs and filenames
                if sintez_link in value:
                    data[key] = value.replace(sintez_link, github_link)
                # if github_filename in data[key]:
                #     data[key] = data[key].replace(github_filename, local_filename)
    
    if os.path.exists(new_archive_path):
        os.remove(new_archive_path)
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    shutil.unpack_archive(archive_path, temp_folder)

    if os.path.exists(custom_packs_temp_path):
        with open(custom_packs_temp_path, 'r') as f:
            print('custom_packs.json found in archive')
            data = json.load(f)
            modify_json_data(data, sintez_link, github_link, local_filename, github_filename)
        with open(custom_packs_temp_path, 'w') as f:
            json.dump(data, f, indent=4)
    
    shutil.make_archive(new_archive_path.replace('.zip', ''), 'zip', root_dir=temp_folder)

    if os.path.exists(custom_packs_temp_path):
        print('custom_packs.json found in archive')
        with open(custom_packs_temp_path, 'r') as f:
            data = json.load(f)
            if 'sintez.io' not in json.dumps(data):
                print('Test passed: sintez.io is replaced in custom_packs.json')
            else:
                print('Test failed: sintez.io is not replaced in custom_packs.json')
    else:
        print('No custom_packs.json in archive')

    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)

    return new_archive_path
