import os
import sys
import time
import psutil
import shutil
from datetime import datetime


# Имя файла для логов
log_file = 'updater.txt'


def log(message):
    now = datetime.now()
    current_time = now.strftime("[%Y.%m.%d %H:%M:%S]")
    with open(log_file, mode="a", encoding="utf-8") as f:
        f.write(f"{current_time} {message}\n")


base_directory = '.'


def main(args):
    log("Запуск updater с аргументами: {}".format(args))
    try:
        if len(args) < 2:
            log("Недостаточно аргументов. Использование: python updater.py <new_file_path> <old_file_path>")
            print("Usage: python updater.py <new_file_path> <old_file_path>")
            return

        new_file_path = args[0]
        old_file_path = args[1]
        log("Новые и старые пути файлов: {}, {}".format(new_file_path, old_file_path))
        process_name = os.path.basename(old_file_path).replace(".exe", "")

        log("Завершение процесса {}".format(process_name))
        while True:
            # Проверяем, запущен ли процесс
            processes = [p for p in psutil.process_iter(['name']) if p.info['name'] == f"{process_name}.exe"]
            if not processes:
                break

            # Убиваем все экземпляры процесса
            for process in processes:
                log("Убийство процесса: {}".format(process.info['name']))
                process.kill()

            time.sleep(0.3)

        # Удаляем старый файл, если он существует
        if os.path.exists(old_file_path):
            log("Удаление старого файла: {}".format(old_file_path))
            os.remove(old_file_path)

        # Перемещаем новый файл на место старого
        log("Перемещение нового файла {} в {}".format(new_file_path, old_file_path))
        shutil.move(new_file_path, old_file_path)
        replace_temp_resources_with_resources(base_directory)
        time.sleep(3)

        log("Запуск {}".format(old_file_path))
        os.startfile(old_file_path)
        input()

    except Exception as e:
        log("Произошла ошибка: {}".format(e))
        print(f"An error occurred: {e}")
        input()


def replace_temp_resources_with_resources(base_path):
    temp_resources_path = os.path.join(base_path, 'temp_resources')
    resources_path = os.path.join(base_path, 'resources')

    # Проверяем, существует ли папка resources
    if os.path.exists(resources_path):
        # Удаляем папку resources, если она существует
        log("Удаление папки: {}".format(resources_path))
        shutil.rmtree(resources_path)

    # Проверяем, существует ли папка temp_resources
    if os.path.exists(temp_resources_path):
        # Переименовываем temp_resources в resources
        log("Переименование {} в {}".format(temp_resources_path, resources_path))
        shutil.move(temp_resources_path, resources_path)
    else:
        log("Папка {} не существует.".format(temp_resources_path))


if __name__ == "__main__":
    main(sys.argv[1:])
