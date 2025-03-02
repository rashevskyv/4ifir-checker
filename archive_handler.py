import os
import json
import shutil

def handle_archive(archive_path, local_filename, github_filename, temp_folder='temp', output_folder='archives'):
    """
    Просто розпаковує та пакує архів без будь-яких модифікацій.
    Використовується для контролю цілісності.
    """
    archive_name = os.path.basename(archive_path)
    new_archive_path = os.path.join(output_folder, archive_name)
    
    # Створення тимчасової директорії для роботи з архівом
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)
    
    if os.path.exists(new_archive_path):
        os.remove(new_archive_path)
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    print(f'Extracting {archive_path} to {temp_folder}')
    shutil.unpack_archive(archive_path, temp_folder)
    
    # Просто створити архів без модифікацій
    shutil.make_archive(new_archive_path.replace('.zip', ''), 'zip', root_dir=temp_folder)
    
    print(f'Archive repacked to {new_archive_path}')
    
    # Очистити тимчасову директорію
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)

    return new_archive_path