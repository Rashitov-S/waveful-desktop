import itertools
import os
import shutil
import sqlite3
import sys
import time
from itertools import cycle
from random import randrange

from PyQt6.QtCore import QUrl, pyqtSignal, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtWidgets import QWidget, QApplication, QMainWindow, QDialog, QFileDialog, QLineEdit, QComboBox
from PyQt6.uic.properties import QtCore

from forms import LoginFormUI, MainFormUI, AddTrackDialogUI, MainContentWidgetUI, FavouriteContentWidgetUI
import client


class UserException(Exception):
    pass


class AddTrackDialog(AddTrackDialogUI):
    # окно добавления трека
    def __init__(self):
        super().__init__()
        self.saved = False
        self.music_file = None
        self.album_image = False
        self.art_combo = True
        self.alb_combo = True
        self.update_field()
        self.no_artist.checkStateChanged.connect(self.change_artist_input)
        self.no_album.checkStateChanged.connect(self.change_albums_input)
        self.select_file_button.clicked.connect(self.select_file)
        self.image_button.clicked.connect(self.select_album_image)
        self.accept_button.clicked.connect(self.accept_dialog)
        self.cancel_button.clicked.connect(self.reject)
        self.image_button.setDisabled(True)

    def accept_dialog(self):
        try:
            title = self.title_input.text()
            if not title:
                self.error_label.setText("Укажите название трека")
                return

            album_name = self.get_album_name()
            if not album_name:
                self.error_label.setText("Укажите название альбома")
                return

            destination_music_path = self.copy_music_file()
            if not destination_music_path:
                self.error_label.setText("Укажите музыкальный файл")
                return
            if self.saved:
                destination_album_path = self.album_image
            elif self.album_image:
                destination_album_path = self.copy_album_image()
            else:
                destination_album_path = None

            self.add_artist()
            if not self.alb_combo:
                self.add_album(destination_album_path)
            print("одижидаемое имя:", album_name)
            album_id = self.get_album_id(album_name)
            artist_id = self.get_artist_id()
            client.add_track(title, artist_id, album_id, destination_music_path)
            self.accept()
        except sqlite3.IntegrityError:
            self.error_label.setText("Альбом или исполнитель уже существует")

    def get_artist_id(self):
        if not self.art_combo:
            return client.get_artists(self.artist_input.text())[0][0]
        return self.artist_combobox.currentIndex() + 1

    def get_album_name(self):
        if not self.alb_combo:
            return self.album_input.text()
        return self.album_combobox.currentText()

    def copy_music_file(self):
        if self.music_file:
            res = client.upload_file(self.music_file)
            if res:
                return res
        return False

    def copy_album_image(self):
        if self.album_image:
            res = client.upload_file(self.album_image)
            if res:
                return res
        return False

    def get_album_id(self, album_name):
        print("имя альбома внутри функции:", album_name)
        print(client.get_album_id(album_name))
        return client.get_album_id(album_name)[0] if not self.alb_combo else client.get_album_id(
            self.album_combobox.currentText())[0]

    def select_album_image(self):
        if not self.saved:
            self.album_image, _ = QFileDialog.getOpenFileName(self, "Выбрать обложку альбома", "",
                                                              "Images (*.png *.jpg *jpeg)")

    def select_file(self):
        # выбор трека
        self.select_file_field.clear()
        self.music_file, _ = QFileDialog.getOpenFileName(self, "Выбрать трек", "",
                                                         "Audio Files (*.mp3 *.wav *.ogg *aac)")
        self.select_file_field.setText(self.music_file)
        flag = client.take_album_from_meta(self.music_file)
        if flag:
            self.album_image = flag
            print("путь до картинки альбома из метаданных", flag)
            self.saved = True
            self.image_button.setDisabled(True)

    def add_artist(self):
        # добавление арстиста в бд
        if not self.art_combo:
            artist = self.artist_input.text()
            if artist:
                client.add_artist(artist)

    def add_album(self, path):
        # добавление альбома в бд
        if not self.alb_combo:
            title = self.album_input.text()
        if self.art_combo:
            artist_id = self.artist_combobox.currentIndex() + 1
        else:
            artist_id = client.get_artists(self.artist_input.text())[0][0]
        if title:
            client.add_album(title, artist_id, path)

    def update_field(self):
        self.artist_combobox.currentTextChanged.connect(self.update_album_box)
        self.update_artist_box()
        self.update_album_box()

    def update_artist_box(self):
        self.artist_combobox.clear()
        artists = client.get_artists(False)
        for artist in artists:
            self.artist_combobox.addItem(artist[1])

    def update_album_box(self):
        self.album_combobox.clear()
        artist_id = self.artist_combobox.currentIndex() + 1
        albums = client.get_albums(artist_id)
        for album in albums:
            self.album_combobox.addItem(album[1])

    def change_albums_input(self):
        # метод для ввода альбома
        if self.no_album.isChecked():
            self.image_button.setDisabled(False)
            self.album_input = QLineEdit()
            self.gridLayout.removeWidget(self.album_combobox)
            self.album_input.setMinimumSize(0, 30)
            self.album_combobox.setParent(None)
            self.gridLayout.addWidget(self.album_input, 2, 1)
            self.alb_combo = False

        else:
            self.image_button.setDisabled(True)
            self.album_combobox = QComboBox()
            self.gridLayout.removeWidget(self.album_input)
            self.album_combobox.setMinimumSize(0, 30)
            self.album_input.setParent(None)
            self.gridLayout.addWidget(self.album_combobox, 2, 1)
            self.alb_combo = True

            self.update_field()

    def change_artist_input(self):
        # метод для ввода артиста
        if self.no_artist.isChecked():
            self.artist_input = QLineEdit()
            self.gridLayout.removeWidget(self.artist_combobox)
            self.artist_input.setMinimumSize(0, 30)
            self.artist_combobox.setParent(None)
            self.gridLayout.addWidget(self.artist_input, 1, 1)
            self.art_combo = False

        else:
            self.artist_combobox = QComboBox()
            self.gridLayout.removeWidget(self.artist_input)
            self.artist_combobox.setMinimumSize(0, 30)
            self.artist_input.setParent(None)
            self.gridLayout.addWidget(self.artist_combobox, 1, 1)
            self.art_combo = True

            self.update_field()


class MainWindow(MainFormUI):
    def __init__(self, session_id):
        self.session_id = session_id
        super(MainWindow, self).__init__(self.session_id)
        self.current_widget = self.main_content_widget.playlist_table1
        self.main_playlist = self.current_widget.tracks  # плейлист из данных в бд
        self.main_playlist_rows = cycle(range(0, len(self.main_playlist)))
        self.main_content_widget.upload_track_button.clicked.connect(self.open_add_track_dialog)
        self.main_button.clicked.connect(self.switch_frames)
        self.favourite_button.clicked.connect(self.switch_frames)
        self.search_track_button.clicked.connect(self.switch_frames)
        self.profile_button.clicked.connect(self.switch_frames)
        self.status_bar.play_button.clicked.connect(self.select_from_button)
        # аудиоплеер
        self.current_track_id = -1
        self.volume = 0.5
        self.status_bar.status_widget.volume_slider.setValue(int(self.volume * 100))
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        # текущее состояние плеера
        self.state = self.media_player.playbackState()
        # модели для бд
        # каждую секунду меняем положение слайдера
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.update_slider)
        self.timer.timeout.connect(self.update_time)
        # сигнал из таблицы Главное
        self.main_content_widget.playlist_table1.play_signal_table.connect(self.select_from_table)
        # сигнал из таблицы Избранное
        self.favourite_content_widget.playlist_table2.play_signal_table.connect(self.select_from_table)
        # сигнал из таблицы Поиск
        self.search_content_widget.playlist_table3.play_signal_table.connect(self.select_from_table)

        self.media_player.playbackStateChanged.connect(self.check_state)
        self.status_bar.status_widget.track_slider.actionTriggered.connect(self.slider_moved)
        self.status_bar.status_widget.volume_slider.actionTriggered.connect(self.set_volume)
        self.media_player.playbackStateChanged.connect(self.end_of_media)
        # кнопка для громкости
        self.status_bar.mute_button.clicked.connect(self.mute_volume)
        self.set_volume()
        # переключение на следующий / предыдущий трек
        self.status_bar.next_button.clicked.connect(self.next)
        self.status_bar.previous_button.clicked.connect(self.previous)
        # кнопки повтора и shuffle
        self.repeat = False
        self.shuffle = False
        self.status_bar.repeat_button.clicked.connect(self.set_repeat)
        self.status_bar.shuffle_button.clicked.connect(self.set_shuffle)
        # кнопка лайка и дизлайка
        self.status_bar.add_favourite_button.clicked.connect(self.like)
        # большая кнопка плейлиста
        self.main_content_widget.play_playlist_button.clicked.connect(lambda x: self.start_play(0))
        self.favourite_content_widget.play_playlist_button.clicked.connect(lambda x: self.start_play(1))
        # поиск
        self.search_button.clicked.connect(self.search)
        # выход
        self.profile_content_widget.exit_button.clicked.connect(self.exit)
        client.send_album_images()

    def exit(self):
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()

    def search(self):
        string = self.search_input.text()
        self.search_content_widget.playlist_table3.update_table(string)
        if self.search_content_widget.playlist_table3.rowCount() == 0:
            self.search_content_widget.info_label.show()
        else:
            self.search_content_widget.info_label.hide()
        self.switch_frames(widget=2)

    def start_play(self, widget):
        if (widget == 1 and self.current_widget == self.main_content_widget.playlist_table1) or (
                widget == 0 and self.current_widget == self.favourite_content_widget.playlist_table2):
            self.current_widget = self.main_content_widget.playlist_table1 if widget == 0 else self.favourite_content_widget.playlist_table2
            self.main_playlist = self.current_widget.tracks
            if self.main_playlist:
                self.current_widget.play_track(0, False, widget)
        else:
            self.current_widget = self.main_content_widget.playlist_table1 if widget == 0 else self.favourite_content_widget.playlist_table2
            self.main_playlist = self.current_widget.tracks
            if self.state == QMediaPlayer.PlaybackState.StoppedState:
                widget = 0 if self.current_widget == self.main_content_widget.playlist_table1 else 1
                if self.main_playlist:
                    self.current_widget.play_track(0, False, widget)
            else:
                self.select_from_button()

    def like(self):
        if not client.get_favorite_track(self.session_id, self.current_track_id):
            client.add_favorite_track(self.session_id, self.current_track_id)
            self.status_bar.add_favourite_button.change_icon("resources\\icons\\liked_icon.png",
                                                             "resources\\icons\\liked_icon.png")
        else:
            client.delete_favorite_track(self.session_id, self.current_track_id)
            self.status_bar.add_favourite_button.change_icon("resources\\icons\\like_icon_normal.png",
                                                             "resources\\icons\\like_icon_hover.png")

    def set_shuffle(self):
        if not self.shuffle:
            self.shuffle = True
            self.status_bar.shuffle_button.change_icon("resources\\icons\\shuffle_true_icon_normal.png",
                                                       "resources\\icons\\shuffle_true_icon_hover.png")
        else:
            self.shuffle = False
            self.status_bar.shuffle_button.change_icon("resources\\icons\\shuffle_icon_normal.png",
                                                       "resources\\icons\\shuffle_icon_hover.png")

    def set_repeat(self):
        if not self.repeat:
            self.repeat = True
            self.status_bar.repeat_button.change_icon("resources\\icons\\repeat_once_icon_normal.png",
                                                      "resources\\icons\\repeat_once_icon_hover.png")
        else:
            self.repeat = False
            self.status_bar.repeat_button.change_icon("resources\\icons\\repeat_icon_normal.png",
                                                      "resources\\icons\\repeat_icon_hover.png")

    def end_of_media(self):
        if self.current_widget == self.main_content_widget.playlist_table1:
            widget = 0
        elif self.current_widget == self.favourite_content_widget.playlist_table2:
            widget = 1
        elif self.current_widget == self.search_content_widget.playlist_table3:
            widget = 2
        current_time = self.status_bar.status_widget.current_label.text()
        end_time = self.status_bar.status_widget.duration_label.text()
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.StoppedState and current_time[
                                                                                            :-1] == end_time[:-1]:
            if self.repeat:
                self.current_widget.play_track(
                    self.current_widget.cur_track, False, widget)
            else:
                self.next()

    def next(self):
        if self.current_widget == self.main_content_widget.playlist_table1:
            widget = 0
        elif self.current_widget == self.favourite_content_widget.playlist_table2:
            widget = 1
        elif self.current_widget == self.search_content_widget.playlist_table3:
            widget = 2
        if not self.shuffle:
            if self.current_widget.cur_track == len(self.main_playlist) - 1:
                self.current_widget.play_track(0, False, widget)
            else:
                self.current_widget.play_track(
                    self.current_widget.cur_track + 1,
                    False, widget)
        else:
            self.current_widget.play_track(randrange(0, len(self.main_playlist)), False, widget)

    def previous(self):
        if self.current_widget == self.main_content_widget.playlist_table1:
            widget = 0
        elif self.current_widget == self.favourite_content_widget.playlist_table2:
            widget = 1
        elif self.current_widget == self.search_content_widget.playlist_table3:
            widget = 2
        if self.current_widget.cur_track == 0:
            self.current_widget.play_track(len(self.main_playlist) - 1, False, widget)
        else:
            self.current_widget.play_track(self.current_widget.cur_track - 1,
                                           False, widget)

    def mute_volume(self):
        if self.audio_output.volume() != 0.0:
            self.audio_output.setVolume(0.0)
            self.status_bar.status_widget.volume_slider.setValue(0)
            self.status_bar.change_volume_icon(0)
        else:
            self.status_bar.change_volume_icon(self.volume * 100)
            self.audio_output.setVolume(self.volume)
            self.status_bar.status_widget.volume_slider.setValue(int(self.volume * 100))

    def set_volume(self):
        self.volume = self.status_bar.status_widget.volume_slider.value() / 100
        self.audio_output.setVolume(self.volume)
        self.status_bar.change_volume_icon(self.volume * 100)

    def change_icons(self):
        # метод для замены иконок на паузу / играть
        if self.state == QMediaPlayer.PlaybackState.PlayingState:
            self.status_bar.play_button.change_icon("resources\\icons\\pause_track_icon.png",
                                                    "resources\\icons\\pause_track_icon.png")
            if self.current_widget == self.main_content_widget.playlist_table1:
                self.main_content_widget.play_playlist_button.change_icon("resources\\icons\\pause_track_icon.png",
                                                                          "resources\\icons\\pause_track_icon.png")
            elif self.current_widget == self.favourite_content_widget.playlist_table2:
                self.favourite_content_widget.play_playlist_button.change_icon("resources\\icons\\pause_track_icon.png",
                                                                               "resources\\icons\\pause_track_icon.png")

        elif self.state == QMediaPlayer.PlaybackState.PausedState:
            self.status_bar.play_button.change_icon("resources\\icons\\play_track_icon_normal.png",
                                                    "resources\\icons\\play_track_icon_normal.png")
            if self.current_widget == self.main_content_widget.playlist_table1:
                self.main_content_widget.play_playlist_button.change_icon(
                    "resources\\icons\\play_track_icon_normal.png",
                    "resources\\icons\\play_track_icon_normal.png")
            elif self.current_widget == self.favourite_content_widget.playlist_table2:
                self.favourite_content_widget.play_playlist_button.change_icon(
                    "resources\\icons\\play_track_icon_normal.png",
                    "resources\\icons\\play_track_icon_normal.png")

    def check_state(self):
        # проверка состояния плеера
        self.state = self.media_player.playbackState()
        self.main_content_widget.playlist_table1.playing = self.state
        self.favourite_content_widget.playlist_table2.playing = self.state
        self.search_content_widget.playlist_table3.playing = self.state
        self.change_icons()

    def select_from_button(self):
        # если нажали играть с кнопки
        if self.state == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        elif self.state == QMediaPlayer.PlaybackState.PausedState:
            self.resume()

    def select_from_table(self, id, widget):
        # если нажали играть с таблицы
        if widget == 0:
            self.current_widget = self.main_content_widget.playlist_table1
        elif widget == 1:
            self.current_widget = self.favourite_content_widget.playlist_table2
        elif widget == 2:
            self.current_widget = self.search_content_widget.playlist_table3
        self.main_playlist = self.current_widget.tracks
        if widget == 0:
            self.favourite_content_widget.playlist_table2.reset_cur_track()
            self.search_content_widget.playlist_table3.reset_cur_track()
        if widget == 1:
            self.main_content_widget.playlist_table1.reset_cur_track()
            self.search_content_widget.playlist_table3.reset_cur_track()
        if widget == 2:
            self.main_content_widget.playlist_table1.reset_cur_track()
            self.favourite_content_widget.playlist_table2.reset_cur_track()
        if self.state == QMediaPlayer.PlaybackState.StoppedState:
            self.play(id)
        elif self.state == QMediaPlayer.PlaybackState.PlayingState:
            if self.current_track_id == id:
                self.pause()
            else:
                self.play(id)
        elif self.state == QMediaPlayer.PlaybackState.PausedState:
            if self.current_track_id == id:
                self.resume()
            else:
                self.play(id)

    def play(self, id):
        track_info = client.get_tracks(id)[0]
        artist_info = client.get_artist_name(track_info[2])
        album_all = client.get_album_all(track_info[3])
        album_path = album_all[1]
        print(album_path)

        client.download_file(track_info[4])
        self.media_player.setSource(QUrl.fromLocalFile(f"resources\\{track_info[4]}"))
        self.current_track_id = id
        self.media_player.play()
        self.status_bar.display(track_info[1], artist_info[0], album_path, client.get_track_length(track_info[4]),
                                self.current_track_id, self.session_id)

    def resume(self):
        self.media_player.play()

    def pause(self):
        self.media_player.pause()

    def update_slider(self):
        if self.state == QMediaPlayer.PlaybackState.PlayingState:
            self.status_bar.status_widget.track_slider.setMinimum(0)
            self.status_bar.status_widget.track_slider.setMaximum(self.media_player.duration())
            self.status_bar.status_widget.track_slider.setValue(self.media_player.position())

    def slider_moved(self):
        self.media_player.setPosition(self.status_bar.status_widget.track_slider.value())
        self.update_time()

    def update_time(self):
        position = self.media_player.position()
        current_time = str(f'{int(position / 60000)}:{int((position / 1000) % 60):02}')
        self.status_bar.status_widget.current_label.setText(current_time)

    def switch_frames(self, widget=None):
        # замена окон главное, избранное, поиск, профиль
        if not widget:
            self.stacked_widget.setCurrentIndex(self.sender().widget_index())
            if self.sender().widget_index() == 1:
                self.favourite_content_widget.playlist_table2.update_table()
            elif self.sender().widget_index() == 0:
                self.main_content_widget.playlist_table1.update_table()
            elif self.sender().widget_index() == 2:
                self.search_content_widget.playlist_table3.update_table()
        else:
            self.stacked_widget.setCurrentIndex(widget)

    def open_add_track_dialog(self):
        self.dialog = AddTrackDialog()
        self.dialog.exec()
        self.main_content_widget.playlist_table1.update_table()

    def closeEvent(self, event):
        self.media_player.stop()
        self.media_player.setSource(QUrl())
        clear_directory("resources\\upload\\tracks")
        clear_directory("resources\\temp")
        event.accept()


class LoginWindow(LoginFormUI):
    def __init__(self):
        super(LoginWindow, self).__init__()
        # подключаем модель для взаимодействия с бд
        self.enter_button.clicked.connect(self.enter)
        client.send_album_images()

    def enter(self):
        login = self.login_input.text()
        password = self.password_input.text()
        try:
            # если ничего не введено - вызываем ошибку
            if not login or not password:
                raise UserException
            user = self.is_user_exist(login)
            if user:
                if user[2] == password:
                    self.set_message_label("Успешный вход", "Green")
                    self.session = MainWindow(user[0])
                    self.hide()
                    self.session.show()
                else:
                    # неверный пароль
                    self.highlight_fields()
                    self.set_message_label("Неверный логин или пароль", "Red")
            else:
                # неверный логин
                self.highlight_fields()
                self.set_message_label("Неверный логин или пароль", "Red")
        except UserException:
            self.highlight_fields()
            self.set_message_label("Ошибка ввода", "Red")

    def on_label_click(self, event):
        self.register()

    def register(self):
        login = self.login_input.text() if self.login_input.text() != "" else False
        password = self.password_input.text() if self.password_input.text() else False
        try:
            # если ничего не введено - вызываем ошибку
            if not login or not password:
                raise UserException
            user = self.is_user_exist(login)
            # если такого пользователя нет - можем регистрировать
            if not user:
                client.add_user(login, password)
                self.set_message_label("Пользователь зарегистрирован", "Green")
            else:
                self.highlight_fields()
                self.set_message_label("Пользователь с таким именем уже существует!", "Red")
        except UserException:
            self.highlight_fields()
            self.set_message_label("Ошибка ввода", "Red")

    def is_user_exist(self, login):
        # проверка на наличие пользователя в бд
        user = client.get_user(login)
        return user if user is not None else False

    def closeEvent(self, event):
        clear_directory("resources\\upload\\tracks")
        clear_directory("resources\\temp")
        event.accept()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


def clear_directory(directory_path):
    # проверка, существует ли директория
    if os.path.exists(directory_path) and os.path.isdir(directory_path):
        # перебор всех файлов и подкаталогов в директории
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)  # удаление файла
                    print(f"Удален файл: {file_path}")
            except Exception as e:
                print(f"Ошибка при удалении {file_path}: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
