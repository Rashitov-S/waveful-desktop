import os
import subprocess
import sys
import time
import psutil
import shutil

base_directory = '.'


def main(args):
    print(args)
    try:
        if len(args) < 2:
            print("Usage: python updater.py <new_file_path> <old_file_path>")
            return

        new_file_path = args[0]
        old_file_path = args[1]
        process_name = os.path.basename(old_file_path).replace(".exe", "")

        print("Terminate process!")
        while True:
            # Check if the process is running
            processes = [p for p in psutil.process_iter(['name']) if p.info['name'] == f"{process_name}.exe"]
            if not processes:
                break

            # Kill all instances of the process
            for process in processes:
                process.kill()

            time.sleep(0.3)

        # Delete the old file if it exists
        if os.path.exists(old_file_path):
            os.remove(old_file_path)

        # Move the new file to the old file's location
        shutil.move(new_file_path, old_file_path)
        replace_temp_resources_with_resources(base_directory)
        time.sleep(1)

        print(f"Starting {old_file_path}")
        print(sys.argv[1])
        os.startfile("Waveful_update.exe")

    except Exception as e:
        print(f"An error occurred: {e}")


def replace_temp_resources_with_resources(base_path):
    temp_resources_path = os.path.join(base_path, 'temp_resources')
    resources_path = os.path.join(base_path, 'resources')

    # Проверяем, существует ли папка resources
    if os.path.exists(resources_path):
        # Удаляем папку resources, если она существует
        shutil.rmtree(resources_path)
        print(f"Удалена папка: {resources_path}")

    # Проверяем, существует ли папка temp_resources
    if os.path.exists(temp_resources_path):
        # Переименовываем temp_resources в resources
        shutil.move(temp_resources_path, resources_path)
        print(f"Папка {temp_resources_path} переименована в {resources_path}.")
    else:
        print(f"Папка {temp_resources_path} не существует.")


if __name__ == "__main__":
    main(sys.argv[1:])
