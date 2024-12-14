import os
import time
from mutagen import File
from mutagen.id3 import APIC
import requests
import zipfile
import requests_cache

requests_cache.install_cache('http_cache', expire_after=18000)
BASE_URL = 'http://127.0.0.1:5002'


def get_version():
    response = requests.get(f'{BASE_URL}/version')
    print(response.json())
    return response.json()


def take_album_from_meta(audio_file, image_temp="resources\\temp\\temp"):
    audio = File(audio_file)
    # проверяем наличие тегов
    if audio is not None and audio.tags is not None:
        for tag in audio.tags.values():
            if isinstance(tag, APIC):
                mime_type = tag.mime
                if mime_type == 'image/jpeg' or mime_type == 'image/jpg':
                    extension = '.jpg'
                elif mime_type == 'image/png':
                    extension = '.png'
                else:
                    print(f"Неизвестный формат изображения: {mime_type}")
                    return False
                image_temp_full = image_temp + extension
                os.makedirs(os.path.dirname(image_temp_full), exist_ok=True)
                with open(image_temp_full, 'wb') as img:
                    img.write(tag.data)
                uploaded_file_path = upload_file(image_temp_full)
                if uploaded_file_path:
                    send_album_images()
                return uploaded_file_path
    print("Обложка альбома не найдена.")
    return False


def upload_file(file_path):
    with open(file_path, 'rb') as file:
        response = requests.post(f'{BASE_URL}/upload', files={'file': file})
        result = response.json()
        if response.status_code == 200:
            print("Файл успешно загружен")
            return result.get('file_path')
        else:
            print("Ошибка загрузки файла", result.get('file_path'))
            return False


def download_update(version):
    response = requests.get(f'{BASE_URL}/upload/{version}')
    if response.status_code == 200:
        filepath = ""
        with open(filepath, 'wb') as f:
            f.write(response.content)
    else:
        return False
    try:
        with zipfile.ZipFile(f"{version}.zip", 'r') as zip_ref:
            zip_ref.extractall("")
        os.remove(f"{version}.zip")
        print(f"Архив {f"{version}.zip"} был удален.")
        return True
    except FileNotFoundError:
        print("ZIP-архив не найден.")
        return False
    except zipfile.BadZipFile:
        print("Ошибка: файл не является корректным ZIP-архивом.")
        return False
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return False


def download_file(file_path):
    print("скачивание:", file_path)
    response = requests.get(f'{BASE_URL}/upload/{file_path}')
    if response.status_code == 200:
        filepath = f"resources\\{file_path}"
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print(f'File {filepath} downloaded successfully')
    else:
        print(f'Failed to download file: {response.text}')


def send_album_images():
    images = get_album_images()
    files = os.listdir("resources\\upload\\album_images")
    if len(files) - 1 < len(images):
        for image in images:
            file_name_with_extension = os.path.basename(image[0])
            file_exist = os.path.isfile(f"resources\\upload\\album_images\\{file_name_with_extension}")
            if not file_exist:
                print(image, "файла не существует")
                download_file(image[0])


def get_track_length(file_path):
    print(file_path)
    response = requests.get(f'{BASE_URL}/length/{file_path}')
    print(f"Статус код: {response.status_code}")
    print(response.json())
    return response.json()


def add_user(login, password):
    response = requests.post(f'{BASE_URL}/users', json={'login': login, 'password': password})
    print(response.json())


def get_user(login):
    response = requests.get(f'{BASE_URL}/users/{login}', params={'nocache': time.time()})
    print(response.json())
    return response.json()


def get_user_by_id(user_id):
    response = requests.get(f'{BASE_URL}/users/{user_id}', params={'nocache': time.time()})
    print(response.json())
    return response.json()


def change_user_password(user_id, new_password):
    response = requests.put(f'{BASE_URL}/users/{user_id}/password', json={'new_password': new_password})
    print(response.json())


def add_album(title, artist_id, path=None):
    response = requests.post(f'{BASE_URL}/albums', json={'title': title, 'artist_id': artist_id, 'path': path})
    print(response.json())


def get_albums(artist_id):
    response = requests.get(f'{BASE_URL}/albums/artist/{artist_id}')
    print(response.json())
    return response.json()


def get_album_id(title):
    response = requests.get(f'{BASE_URL}/albums/title/{title}')
    print(response.json())
    return response.json()


def get_album_all(album_id):
    response = requests.get(f'{BASE_URL}/albums/{album_id}')
    return response.json()


def get_album_images():
    response = requests.get(f'{BASE_URL}/albums/all_images')
    return response.json()


def add_artist(name):
    response = requests.post(f'{BASE_URL}/artists', json={'name': name})
    print(response.json())


def get_artists(name=None, artist_id=None):
    params = {}
    if name:
        params['name'] = name
    if artist_id:
        params['artist_id'] = artist_id
    response = requests.get(f'{BASE_URL}/artists', params=params)
    print(response.json())
    return response.json()


def get_artist_name(artist_id):
    response = requests.get(f'{BASE_URL}/artists/{artist_id}')
    print(response.json())
    return response.json()


def add_track(title, artist_id, album_id, path):
    response = requests.post(f'{BASE_URL}/tracks',
                             json={'title': title, 'artist_id': artist_id, 'album_id': album_id, 'path': path})
    print(response.json())


def get_tracks_all():
    response = requests.get(f'{BASE_URL}/tracks/all', params={'nocache': time.time()})
    return response.json()


def get_tracks(track_id=None, title=None):
    params = {}
    if track_id:
        params['track_id'] = track_id
    if title:
        params['title'] = title
    response = requests.get(f'{BASE_URL}/tracks', params={**params, 'nocache': time.time()})
    print(response.json())
    return response.json()


def get_search_track(title):
    response = requests.get(f'{BASE_URL}/tracks/{title}', params={'nocache': time.time()})
    print(response.json())
    return response.json()


def get_max_id():
    response = requests.get(f'{BASE_URL}/tracks/max_id', params={'nocache': time.time()})
    print(response.json())
    return response.json()


def add_favorite_track(user_id, track_id):
    response = requests.post(f'{BASE_URL}/favorites', json={'user_id': user_id, 'track_id': track_id}, timeout=1,
                             params={'nocache': time.time()})
    print(response.json())


def get_favorite_tracks(user_id):
    response = requests.get(f'{BASE_URL}/favorites/{user_id}', params={'nocache': time.time()})
    print(response.json())
    return response.json()


def get_favorite_track(user_id, track_id):
    response = requests.get(f'{BASE_URL}/favorites/{user_id}/{track_id}', params={'nocache': time.time()})
    print(response.json())
    print(response.from_cache)
    return response.json()


def delete_favorite_track(user_id, track_id):
    response = requests.delete(f'{BASE_URL}/favorites', json={'user_id': user_id, 'track_id': track_id}, timeout=1,
                               params={'nocache': time.time()})
    print(response.json())


def check_health():
    response = requests.get(f'{BASE_URL}', timeout=20)
    print(response.json())
