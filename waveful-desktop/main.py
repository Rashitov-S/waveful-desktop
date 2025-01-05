import itertools
import os
import shutil
import sqlite3
import sys
import time
from itertools import cycle
from random import randrange

from PyQt6.QtCore import QUrl, pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtWidgets import QWidget, QApplication, QMainWindow, QDialog, QFileDialog, QLineEdit, QComboBox
from PyQt6.uic.properties import QtCore

from forms import LoginFormUI, MainFormUI, AddTrackDialogUI, MainContentWidgetUI, FavouriteContentWidgetUI
import client
import subprocess
from __version__ import __version__


class UserException(Exception):
    pass


class AddTrackDialog(AddTrackDialogUI):
    # окно добавления трека
    def __init__(self):
        super().__init__()
        self.music_file = None
        self.metadata = {}
        self.artists = {}
        self.searched_artists = {}
        self.albums = {}
        self.searched_albums = {}
        self.album_image = False
        self.art_combo = True
        self.alb_combo = True
        self.update_field()
        self.no_artist.checkStateChanged.connect(self.change_artist_input)
        self.no_album.checkStateChanged.connect(self.change_albums_input)
        self.select_file_button.clicked.connect(self.select_file)
        self.search_artist_input.textChanged.connect(self.search_artist)
        self.search_album_input.textChanged.connect(self.search_albums)
        self.title_input.textChanged.connect(lambda: self.check_tabs(1))
        self.artist_input.textChanged.connect(lambda: self.check_tabs(2))
        self.artist_combobox.activated.connect(lambda: self.check_tabs(2))
        self.search_artist_input.textChanged.connect(lambda: self.check_tabs(2))
        self.album_input.textChanged.connect(lambda: self.check_tabs(3))
        self.album_combobox.activated.connect(lambda: self.check_tabs(3))
        self.search_album_input.textChanged.connect(lambda: self.check_tabs(3))
        self.tabs.setTabVisible(1, False)
        self.tabs.setTabVisible(2, False)
        self.tabs.setTabVisible(3, False)
        # self.artist_combobox.currentTextChanged.connect(self.update_album_box)
        self.tabs.currentChanged.connect(lambda: self.update_album_box(True))
        self.image_button.clicked.connect(self.select_album_image)
        self.accept_button.clicked.connect(self.accept_dialog)
        self.cancel_button.clicked.connect(self.reject)
        self.artist_input.hide()
        self.album_input.hide()
        self.image_button.hide()

    def search_artist(self):
        if not self.search_artist_input.text():
            for artist in self.artists.keys():
                self.artist_combobox.addItem(artist)
        else:
            self.artist_combobox.clear()
            self.searched_artists = {v: k for v, k in self.artists.items() if
                                     self.search_artist_input.text().lower() in v.lower()}

            print(self.artists)
            for artist in self.searched_artists.keys():
                self.artist_combobox.addItem(artist)

    def search_albums(self):
        if not self.search_album_input.text():
            for album in self.albums.keys():
                self.album_combobox.addItem(album)
        else:
            self.album_combobox.clear()
            print(self.albums)
            self.searched_albums = {v: k for v, k in self.albums.items() if
                                    self.search_album_input.text().lower() in v.lower()}

            for album in self.searched_albums.keys():
                self.album_combobox.addItem(album)

    def select_album_image(self):
        try:
            self.album_image, _ = QFileDialog.getOpenFileName(self, "Выбрать обложку альбома", "",
                                                              "Images (*.png *.jpg *jpeg)")
            pixmap = QPixmap(self.album_image)
            self.image_preview.setPixmap(pixmap.scaled(self.image_preview.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                                       Qt.TransformationMode.SmoothTransformation))
        except Exception:
            pass

    def select_file(self):
        # выбор трека
        try:
            self.select_file_field.clear()
            self.music_file, _ = QFileDialog.getOpenFileName(self, "Выбрать трек", "",
                                                             "Audio Files (*.mp3 *.wav *.ogg *aac)")
            self.select_file_field.setText(self.music_file)
            self.metadata = client.extract_metadata(self.music_file)
            self.album_image = client.take_album_from_meta(self.music_file)
            self.check_tabs(1)
        except Exception:
            pass

        # if flag:
        #     self.album_image = flag
        #     print("путь до картинки альбома из метаданных", flag)
        #     self.saved = True
        #     self.image_button.setDisabled(True)

    def check_tabs(self, index):
        match index:
            case 1:
                if self.title_input.text() and self.music_file:
                    self.tabs.setTabVisible(1, True)
                    if self.metadata.get("artist", None):
                        self.meta.setText(f"Исполнитель из метаданных: {self.metadata.get("artist", None)}")
                else:
                    self.tabs.setTabVisible(1, False)
                    self.tabs.setTabVisible(2, False)
                    self.tabs.setTabVisible(3, False)
            case 2:
                print("тексты", self.artist_combobox.currentText(), self.artist_input.text())
                print("проверка", self.art_combo, self.artist_combobox.currentText(), self.artist_input.text())
                if (self.artist_combobox.currentText() and self.art_combo) or (
                        self.artist_input.text() and not self.art_combo):
                    self.tabs.setTabVisible(2, True)
                    # self.update_field()
                    if self.metadata.get("album", None):
                        self.meta_album.setText(f"Альбом из метаданных: {self.metadata.get("album", None)}")
                        self.album_input.setText(f"{self.metadata.get("album", None)}")
                else:
                    self.tabs.setTabVisible(2, False)
                    self.tabs.setTabVisible(3, False)
            case 3:
                if (self.album_combobox.currentText() and self.alb_combo) or (
                        self.album_input.text() and not self.alb_combo):
                    self.tabs.setTabVisible(3, True)
                    if self.album_image and not self.alb_combo:
                        pixmap = QPixmap(self.album_image)
                        self.image_preview.setPixmap(
                            pixmap.scaled(self.image_preview.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation))
                    else:
                        self.image_preview.clear()
                else:
                    self.tabs.setTabVisible(3, False)

    def accept_dialog(self):
        title = self.title_input.text()
        artist = self.artist_combobox.currentText() if self.art_combo else self.artist_input.text()
        album = self.album_combobox.currentText() if self.alb_combo else self.album_input.text()
        file = self.copy_music_file()
        if not self.art_combo:
            self.add_artist()
        artist_id = self.artists[artist] if self.art_combo else client.get_artists(name=artist)[0][0]
        if not self.alb_combo:
            album_path = self.copy_album_image()
            self.add_album(album, artist_id, album_path)
        album_id = self.albums[album] if self.alb_combo else client.get_album_id(album)[0]
        print(title, artist_id, album_id, file)
        client.add_track(title, artist_id, album_id, file)
        self.accept()

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

    def add_artist(self):
        # добавление арстиста в бд
        if not self.art_combo:
            artist = self.artist_input.text()
            if artist:
                client.add_artist(artist)

    def add_album(self, title, artist_id, path):
        client.add_album(title, artist_id, path)

    def update_field(self):
        print("вызов серверного обновления боксов")
        self.update_artist_box()
        self.update_album_box()

    def update_artist_box(self):
        print("вызов серверного обновления артистов")
        self.artist_combobox.clear()
        self.artists = {v: k for k, v in dict(client.get_artists(False)).items()}
        for artist in self.artists.keys():
            self.artist_combobox.addItem(artist)

    def update_album_box(self, index=False):
        if index:
            index = self.tabs.currentIndex()
        if index is False or index == 2:
            if self.artist_combobox.currentText():
                self.album_combobox.clear()
                artist_id = self.artists[self.artist_combobox.currentText()]
                self.albums = {v: k for k, v in dict(client.get_albums(artist_id)).items()}
                print(self.albums)
                for key in self.albums.keys():
                    self.album_combobox.addItem(key)
            if not self.art_combo:
                self.album_combobox.clear()

    def change_albums_input(self):
        self.search_album_input.clear()
        # метод для ввода альбома
        if self.no_album.isChecked():
            self.album_combobox.clear()
            self.album_input.show()
            self.search_album_input.hide()
            self.album_combobox.hide()
            self.image_button.show()
            self.alb_combo = False

        else:
            self.album_combobox.show()
            self.search_album_input.show()
            self.album_input.hide()
            self.image_button.hide()
            self.alb_combo = True

            self.update_field()

        if self.album_image and not self.alb_combo:
            pixmap = QPixmap(self.album_image)
            self.image_preview.setPixmap(
                pixmap.scaled(self.image_preview.size(), Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation))
        else:
            self.image_preview.clear()

        self.check_tabs(3)

    def change_artist_input(self):
        self.search_artist_input.clear()
        # self.artist_input.clear()
        # метод для ввода артиста
        if self.no_artist.isChecked():
            self.artist_combobox.clear()
            self.artist_input.show()
            self.search_artist_input.hide()
            self.artist_combobox.hide()

            self.no_album.hide()
            self.search_album_input.hide()
            self.album_combobox.hide()
            self.album_input.show()
            self.image_button.show()

            self.art_combo = False
            self.alb_combo = False

        else:
            self.artist_combobox.show()
            self.search_artist_input.show()
            self.artist_input.hide()

            self.no_album.show()
            self.search_album_input.show()
            self.album_combobox.show()
            self.album_input.hide()
            self.image_button.hide()

            self.art_combo = True
            self.alb_combo = True

            if self.artist_combobox.currentText():
                self.album_combobox.clear()
                artist_id = self.artists[self.artist_combobox.currentText()]
                for key in self.albums.keys():
                    self.album_combobox.addItem(key)
            if not self.art_combo:
                self.album_combobox.clear()

        if self.album_image and not self.alb_combo:
            pixmap = QPixmap(self.album_image)
            self.image_preview.setPixmap(
                pixmap.scaled(self.image_preview.size(), Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation))
        else:
            self.image_preview.clear()
        self.check_tabs(2)


class MainWindow(MainFormUI):
    def __init__(self, session_id):
        self.session_id = session_id
        super(MainWindow, self).__init__(self.session_id)
        # проверка обновлений
        if check_version():
            self.init_update()
        self.current_widget = self.main_content_widget.playlist_table1
        self.main_playlist = self.current_widget.tracks  # плейлист из данных в бд
        self.main_playlist_rows = cycle(range(0, len(self.main_playlist)))
        self.main_content_widget.upload_track_button.clicked.connect(self.open_add_track_dialog)
        self.main_button.clicked.connect(self.switch_frames)
        self.favourite_button.clicked.connect(self.switch_frames)
        self.search_track_button.clicked.connect(self.switch_frames)
        self.profile_button.clicked.connect(self.switch_frames)
        self.status_bar.play_button.clicked.connect(self.select_from_button)
        self.fullscreen_overlay.play_button.clicked.connect(self.select_from_button)
        # аудиоплеер
        self.current_track_id = -1
        self.volume = 0.5
        self.status_bar.status_widget.volume_slider.setValue(int(self.volume * 100))
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        # открытие фулл-экранного режима
        self.status_bar.maximize_button.clicked.connect(self.check_fullscreen_overlay)
        # текущее состояние плеера
        self.state = self.media_player.playbackState()
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
        self.status_bar.status_widget.track_slider.actionTriggered.connect(
            lambda _: self.slider_moved(self.status_bar.status_widget.track_slider))
        self.fullscreen_overlay.track_slider.actionTriggered.connect(
            lambda _: self.slider_moved(self.fullscreen_overlay.track_slider))
        self.status_bar.status_widget.volume_slider.actionTriggered.connect(self.set_volume)
        self.media_player.playbackStateChanged.connect(self.end_of_media)
        # кнопка для громкости
        self.status_bar.mute_button.clicked.connect(self.mute_volume)
        self.set_volume()
        # переключение на следующий / предыдущий трек
        self.status_bar.next_button.clicked.connect(self.next)
        self.status_bar.previous_button.clicked.connect(self.previous)
        self.fullscreen_overlay.next_button.clicked.connect(self.next)
        self.fullscreen_overlay.previous_button.clicked.connect(self.previous)
        # кнопки повтора и shuffle
        self.repeat = False
        self.shuffle = False
        self.status_bar.repeat_button.clicked.connect(self.set_repeat)
        self.status_bar.shuffle_button.clicked.connect(self.set_shuffle)
        self.fullscreen_overlay.repeat_button.clicked.connect(self.set_repeat)
        self.fullscreen_overlay.shuffle_button.clicked.connect(self.set_shuffle)
        # кнопка лайка и дизлайка
        self.status_bar.add_favourite_button.clicked.connect(self.like)
        # большая кнопка плейлиста
        self.main_content_widget.play_playlist_button.clicked.connect(lambda x: self.start_play(0))
        self.favourite_content_widget.play_playlist_button.clicked.connect(lambda x: self.start_play(1))
        # поиск
        self.search_button.clicked.connect(self.search)
        # выход
        self.profile_content_widget.exit_button.clicked.connect(self.exit)

    def check_fullscreen_overlay(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.show_fullscreen_overlay()
        else:
            self.show_fullscreen_overlay(playing=False)

    def init_update(self):
        self.update_button.show()
        self.update_button.clicked.connect(self.download_update)

    def update_application(self):
        try:
            # запускаем программу обновления
            args = ["Waveful_update.exe", "Waveful.exe"]
            subprocess.Popen(["Updater.exe"] + args)
        except Exception as e:
            print(f"Ошибка обновления: {e}")

    def download_update(self):
        try:
            downloaded = client.download_update(f"{client.get_version()}.zip")
            if downloaded:
                self.update_application()
        except Exception as e:
            print(f"Ошибка скачивания обновления: {e}")

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
            self.fullscreen_overlay.shuffle_button.change_icon("resources\\icons\\shuffle_true_icon_normal.png",
                                                               "resources\\icons\\shuffle_true_icon_hover.png")
        else:
            self.shuffle = False
            self.status_bar.shuffle_button.change_icon("resources\\icons\\shuffle_icon_normal.png",
                                                       "resources\\icons\\shuffle_icon_hover.png")
            self.fullscreen_overlay.shuffle_button.change_icon("resources\\icons\\shuffle_icon_normal.png",
                                                               "resources\\icons\\shuffle_icon_hover.png")

    def set_repeat(self):
        if not self.repeat:
            self.repeat = True
            self.status_bar.repeat_button.change_icon("resources\\icons\\repeat_once_icon_normal.png",
                                                      "resources\\icons\\repeat_once_icon_hover.png")
            self.fullscreen_overlay.repeat_button.change_icon("resources\\icons\\repeat_once_icon_normal.png",
                                                              "resources\\icons\\repeat_once_icon_hover.png")
        else:
            self.repeat = False
            self.status_bar.repeat_button.change_icon("resources\\icons\\repeat_icon_normal.png",
                                                      "resources\\icons\\repeat_icon_hover.png")
            self.fullscreen_overlay.repeat_button.change_icon("resources\\icons\\repeat_icon_normal.png",
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
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.StoppedState and (current_time[
                                                                                             :-1] == end_time[
                                                                                                     :-1] or self.status_bar.status_widget.track_slider.value() / self.status_bar.status_widget.track_slider.maximum() > 0.99):
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
            self.fullscreen_overlay.play_button.change_icon("resources\\icons\\pause_track_icon.png",
                                                            "resources\\icons\\pause_track_icon.png")
            if self.current_widget == self.main_content_widget.playlist_table1:
                self.main_content_widget.play_playlist_button.change_icon(
                    "resources\\icons\\pause_track_icon.png",
                    "resources\\icons\\pause_track_icon.png")
                if self.current_widget.selected_row >= 0 and self.current_widget.selected_row == self.current_widget.cur_track:
                    self.main_content_widget.playlist_table1.cur_button1.change_icon(
                        "resources\\icons\\pause_icon_normal.png",
                        "resources\\icons\\pause_icon_hover.png")
            elif self.current_widget == self.favourite_content_widget.playlist_table2:
                self.favourite_content_widget.play_playlist_button.change_icon(
                    "resources\\icons\\pause_track_icon.png",
                    "resources\\icons\\pause_track_icon.png")
                if self.current_widget.selected_row >= 0 and self.current_widget.selected_row == self.current_widget.cur_track:
                    self.favourite_content_widget.playlist_table2.cur_button1.change_icon(
                        "resources\\icons\\pause_icon_normal.png",
                        "resources\\icons\\pause_icon_hover.png")

        elif self.state == QMediaPlayer.PlaybackState.PausedState:
            self.status_bar.play_button.change_icon("resources\\icons\\play_track_icon_normal.png",
                                                    "resources\\icons\\play_track_icon_normal.png")
            self.fullscreen_overlay.play_button.change_icon("resources\\icons\\play_track_icon_normal.png",
                                                            "resources\\icons\\play_track_icon_normal.png")
            if self.current_widget == self.main_content_widget.playlist_table1:
                self.main_content_widget.play_playlist_button.change_icon(
                    "resources\\icons\\play_track_icon_normal.png",
                    "resources\\icons\\play_track_icon_normal.png")
                if self.current_widget.selected_row >= 0 and self.current_widget.selected_row == self.current_widget.cur_track:
                    self.main_content_widget.playlist_table1.cur_button1.change_icon(
                        "resources\\icons\\play_icon_normal.png",
                        "resources\\icons\\play_icon_hover.png")
            elif self.current_widget == self.favourite_content_widget.playlist_table2:
                self.favourite_content_widget.play_playlist_button.change_icon(
                    "resources\\icons\\play_track_icon_normal.png",
                    "resources\\icons\\play_track_icon_normal.png")
                if self.current_widget.selected_row >= 0 and self.current_widget.selected_row == self.current_widget.cur_track:
                    self.favourite_content_widget.playlist_table2.cur_button1.change_icon(
                        "resources\\icons\\play_icon_normal.png",
                        "resources\\icons\\play_icon_hover.png")

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
            if self.fullscreen_overlay.isVisible():
                self.pause_visualizer()
        elif self.state == QMediaPlayer.PlaybackState.PausedState:
            self.resume()
            if self.fullscreen_overlay.isVisible():
                self.start_visualizer()

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
        print(id)
        track_info = client.get_tracks(id)[0]
        print("проверка", track_info)
        has_track = client.check_track_file(track_info[4])
        print("есть трек:", has_track)
        if not has_track:
            client.download_file(track_info[4])
        self.media_player.setSource(QUrl.fromLocalFile(f"resources\\{track_info[4]}"))
        self.current_track_id = id
        seconds = round(track_info[5])
        duration = f"{seconds // 60}:{seconds % 60:02d}"
        self.media_player.play()
        self.status_bar.display(track_info[1], track_info[7], track_info[11], duration,
                                self.current_track_id, self.session_id)
        self.display_track()
        if self.fullscreen_overlay.isVisible():
            self.start_visualizer()

    def resume(self):
        self.media_player.play()

    def pause(self):
        self.media_player.pause()

    def update_slider(self):
        if self.state == QMediaPlayer.PlaybackState.PlayingState:
            self.status_bar.status_widget.track_slider.setMinimum(0)
            self.status_bar.status_widget.track_slider.setMaximum(self.media_player.duration())
            self.status_bar.status_widget.track_slider.setValue(self.media_player.position())

            self.fullscreen_overlay.track_slider.setMinimum(0)
            self.fullscreen_overlay.track_slider.setMaximum(self.media_player.duration())
            self.fullscreen_overlay.track_slider.setValue(self.media_player.position())

    def slider_moved(self, slider):
        value = slider.value()
        print(value)
        self.media_player.setPosition(value)
        if slider == self.fullscreen_overlay.track_slider:
            self.status_bar.status_widget.track_slider.setValue(value)
        else:
            self.fullscreen_overlay.track_slider.setValue(value)
        self.update_time()

    def update_time(self):
        position = self.media_player.position()
        current_time = str(f'{int(position / 60000)}:{int((position / 1000) % 60):02}')
        self.status_bar.status_widget.current_label.setText(current_time)
        self.fullscreen_overlay.current_label.setText(current_time)

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
        # clear_directory("resources\\upload\\tracks")
        clear_directory("resources\\temp")
        event.accept()


class LoginWindow(LoginFormUI):
    def __init__(self):
        super(LoginWindow, self).__init__()
        # подключаем модель для взаимодействия с бд
        self.enter_button.clicked.connect(self.enter)

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
            self.set_message_label("Ошибка вводаAA", "Red")

    def is_user_exist(self, login):
        # проверка на наличие пользователя в бд
        user = client.get_user(login)
        return user if user is not None else False

    def closeEvent(self, event):
        # clear_directory("resources\\upload\\tracks")
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


def check_version():
    server_version = client.get_version()
    return float(__version__) < float(server_version)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
