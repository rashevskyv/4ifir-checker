import pyzipper
import os
import json
import shutil

def handle_archive(archive_path, temp_folder='github/temp', output_folder='github'):
    archive_name=os.path.basename(archive_path)
    new_archive_path = os.path.join(output_folder, archive_name)
    sintez_link = 'sintez.io/'
    github_link = 'github.com/rashevskyv/4ifir-checker/releases/latest/download/'
    github_link = 'github.com/rashevskyv/4ifir-checker/raw/main/github/'
    custom_packs_path = 'config/aio-switch-updater/custom_packs.json'
    custom_packs_temp_path = os.path.join(temp_folder, custom_packs_path)
    
    # Delete archive_name if it exists at the start of the function
    if os.path.exists(new_archive_path):
        os.remove(new_archive_path)
    
    print(f'Processing {archive_path} for github release...')

    # Check if output_folder exists, if not create it
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Check if temp_folder exists, if not create it
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    # # Check if temp_folder exists, if not create it
    # if not os.path.exists(os.path.dirname(archive_path)):
    #     os.makedirs(os.path.dirname(archive_path))

    # Extract the archive to the temp folder
    with pyzipper.ZipFile(archive_path, 'r') as zip_ref:
        zip_ref.extractall(temp_folder)

    # Navigate to config/aio-switch-updater/ and locate custom_packs.json
    print('Replacing sintez.io links to gihub in custom_packs.json...')

    if os.path.exists(custom_packs_temp_path):
        # Load and modify the JSON data
        with open(custom_packs_temp_path, 'r') as f:
            data = json.load(f)
            # Replace all instances of 'sintez.io' with a placeholder
            json_str = json.dumps(data).replace(sintez_link, github_link)
            modified_data = json.loads(json_str)
        
        # Save the modified JSON data back to custom_packs.json
        with open(custom_packs_temp_path, 'w') as f:
            json.dump(modified_data, f, indent=4)
    
    # Create a new archive with modified files
    print('Creating new archive with github links...')
    with pyzipper.ZipFile(new_archive_path, 'w', compression=pyzipper.ZIP_DEFLATED) as new_zip:
        for root, _, files in os.walk(temp_folder):
            for file in files:
                if file != archive_name:  # Skip adding this file to the new archive
                    file_path = os.path.join(root, file)
                    new_zip.write(file_path, os.path.relpath(file_path, temp_folder))
    
    if os.path.exists(custom_packs_temp_path):
        with open(custom_packs_temp_path, 'r') as f:
            data = json.load(f)
            # Check if 'sintez.io' is replaced
            if 'sintez.io' not in json.dumps(data):
                print('Test passed: sintez.io is replaced in custom_packs.json')
            else:
                print('Test failed: sintez.io is not replaced in custom_packs.json')
    else:
        print('No custom_packs.json in archive')

    shutil.rmtree(temp_folder)

    return new_archive_path