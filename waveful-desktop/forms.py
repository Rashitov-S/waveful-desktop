import random
import sys
import time

from PyQt6.QtCore import Qt, QEvent, QSize, pyqtSignal, QPropertyAnimation, QTimer, QRect, QEasingCurve
from PyQt6.QtGui import QIcon, QPixmap, QColor, QBrush, QFont, QPainter
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtWidgets import QWidget, QApplication, QLineEdit, QPushButton, QMainWindow, QSizePolicy, QVBoxLayout, \
    QScrollArea, QFrame, QStackedWidget, QDialog, QComboBox, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, \
    QAbstractItemView, QAbstractScrollArea, QStatusBar, QHBoxLayout, QLabel, QSpacerItem, QMenu, QToolButton, \
    QGraphicsOpacityEffect, QGraphicsScene, QGraphicsRectItem, QGraphicsView, QStackedLayout, QGraphicsDropShadowEffect
from PyQt6 import uic, QtCore
import io
import client

template_login_form = open("resources/UI/login_formUI.ui", mode="r", encoding="utf-8").read()
template_main_form = open("resources/UI/main_formUI.ui", mode="r", encoding="utf-8").read()
template_main_content_widget = open("resources/UI/main_content_widgetUI.ui", mode="r", encoding="utf-8").read()
template_favourite_content_widget = open("resources/UI/favourite_content_widget.ui", mode="r", encoding="utf-8").read()
template_search_content_widget = open("resources/UI/search_content_widgetUI.ui", mode="r", encoding="utf-8").read()
template_profile_content_widget = open("resources/UI/profile_content_widgetUI.ui", mode="r", encoding="utf-8").read()
template_add_track_dialog = open("resources/UI/add_track_dialog2.ui", mode="r", encoding="utf-8").read()
template_status_bar = open("resources/UI/status_barUI.ui", mode="r", encoding="utf-8").read()
template_about_widget = open("resources/UI/about_widgetUI.ui", mode="r", encoding="utf-8").read()
template_fullscreen_widget = open("resources/UI/fullscreen_widgetUI.ui", mode="r", encoding="utf-8").read()


class MenuListButton(QPushButton):
    # класс для кастомных кнопок в меню слева
    def __init__(self, title, img_path, index):
        super().__init__()
        self.title = title
        self.index = index
        self.img_path = img_path
        self.setIcon(QIcon(img_path))
        self.setIconSize(QSize(64, 64))
        self.setFixedSize(290, 70)
        self.setText(title)
        self.setStyleSheet("""
                    QPushButton {
                        background: #26c9a8;
                        padding: 10px;
                        border-radius: 15%;
                        color: #fff;
                        font-family: Sans-Serif;
                        font-weight: bold;
                        font-size: 20px;
                        text-align: left;
                        text-transform: uppercase;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1: 0, y1: 0.5, x2: 1, y2: 0.5, 
                                            stop: 0 rgba(146, 254, 157, 1), 
                                            stop: 1 rgba(0, 201, 255, 1));
                        border-color: #777;
                    }
                    QPushButton:pressed {
                        background-color: #555;
                        border-color: #888;
                    }
                """)

    def widget_index(self):
        # метод для получения индекса окна
        return self.index


class InterfaceButton(QPushButton):
    # класс для иконок в интерфейсе
    def __init__(self, normal_image, hover_image, parent=None, icon_size=65):
        super().__init__(parent)
        self.setStyleSheet("text-align: center;")
        self.icon_size = icon_size
        self.normal_image = QIcon(normal_image)
        self.hover_image = QIcon(hover_image)
        self.setIconSize(QSize(self.icon_size, self.icon_size))
        self.setIcon(self.normal_image)

    def change_icon(self, normal_image, hover_image):
        try:
            self.normal_image = QIcon(normal_image)
            self.hover_image = QIcon(hover_image)
            self.setIconSize(QSize(self.icon_size, self.icon_size))
            self.setIcon(self.normal_image)
        except RuntimeError as e:
            print("Ошибка:", e.args)

    def enterEvent(self, event):
        self.setIconSize(QSize(self.icon_size + 2, self.icon_size + 2))
        self.setIcon(self.hover_image)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setIcon(self.normal_image)
        self.setIconSize(QSize(self.icon_size, self.icon_size))
        super().leaveEvent(event)


class PlaylistTable(QTableWidget):
    play_signal_table = pyqtSignal(int, int)

    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.tracks_id = []
        self.tracks = []
        self.user_id = user_id
        self.widget = 0
        self.setMouseTracking(True)
        self.setIconSize(QSize(32, 32))
        self.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.highlighted_row = -1
        self.selected_row = -1
        self.playing = QMediaPlayer.PlaybackState.StoppedState
        self.cur_track = -1
        # кнопка играющего трека hover
        self.cur_button = None
        # кнопка играющего трека select
        self.cur_button1 = None
        self.cellClicked.connect(self.select_row)
        self.verticalScrollBar().valueChanged.connect(self.on_scroll)
        self.set_widget()
        self.start = 0
        self.setup_table()

    def on_scroll(self):
        current_value = self.verticalScrollBar().value()
        max_value = self.verticalScrollBar().maximum()
        if current_value == max_value:
            self.add_next_tracks()

    def set_widget(self, widget=0):
        self.widget = widget

    def setup_table(self):
        # убираем индексы
        self.verticalHeader().setVisible(False)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["№", "Трек", "Исполнитель", "Альбом", "Длительность"])
        # указываем размер первого столбца
        self.setColumnWidth(0, 15)
        header = self.horizontalHeader()
        # добавляем растяжение
        for i in range(1, 6):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setRowCount(0)
        self.setStyleSheet("""
                    QTableWidget {
                        background-color: transparent;
                        gridline-color: transparent;
                    }
                    QHeaderView::section {
                        padding: 5px;
                        color: white;
                        background-color: #26c9a8;
                        font-size: 16px;
                    }
                    QTableWidget::item:hover {
                        background-color: rgba(65, 65, 65, 70);
                        border-radius: 5px; 
                        }
                    QTableWidget::item {
                        padding: 0;
                        margin: 0;
                    }
                    QTableWidget::item:selected {
                        background-color: gray;
                        color: white;
                        border-radius: 5px;
                    }
                """)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.update_table()

    def select_row(self, row, column):
        self.clear_selection()
        if self.selected_row == -1:
            self.selected_row = row
            try:
                self.item(row, 0).setText("")
            except AttributeError:
                pass
            for i in range(self.columnCount()):
                item = self.item(row, i)
                try:
                    item.setData(Qt.ItemDataRole.BackgroundRole, QBrush(QColor("#cdcdcd")))
                except AttributeError:
                    pass
            button = InterfaceButton("resources\\icons\\play_icon_normal.png", "resources\\icons\\play_icon_hover.png",
                                     icon_size=16)
            button.setStyleSheet("""
                                                                QPushButton {
                                                                    background-color: transparent;  /* Делаем фон прозрачным */
                                                                    border: none;                   /* Убираем границу */
                                                                }
                                                            """)
            button.clicked.connect(lambda x: self.play_track(item.row(), button, self.widget))
            if self.cur_track == row:
                self.cur_button1 = button
                if (self.playing == QMediaPlayer.PlaybackState.StoppedState or
                        self.playing == QMediaPlayer.PlaybackState.PlayingState):
                    self.cur_button1.change_icon("resources\\icons\\pause_icon_normal.png",
                                                 "resources\\icons\\pause_icon_hover.png")
            self.setCellWidget(self.selected_row, 0, button)

    def update_table(self):
        self.tracks_id = []
        self.setRowCount(0)
        tracks = client.get_tracks_all(self.start)
        self.tracks = tracks
        num = 1
        images = [[x[11]] for x in tracks]
        print(len(images))
        client.send_album_images(images)
        for track in tracks:
            self.tracks_id.append(track[0])
            seconds = round(track[5])
            duration = f"{seconds // 60}:{seconds % 60:02d}"
            self.add_track(str(num), track[1], track[7],
                           track[9], duration, "resources/" + track[11])
            self.setRowHeight(num - 1, 40)
            num += 1
        fnt = self.font()
        fnt.setPointSize(11)
        self.setFont(fnt)

    def add_next_tracks(self):
        next = client.get_next_tracks(self.start)
        if next:
            self.tracks = self.tracks + next
            self.start += 30
            self.update_table()

    def add_track(self, num, title, artist, album, duration, path):
        row_position = self.rowCount()
        self.insertRow(row_position)
        num = QTableWidgetItem(num)
        title = QTableWidgetItem(title)

        album_img = QIcon(path)
        title.setIcon(album_img)
        artist = QTableWidgetItem(artist)
        album = QTableWidgetItem(album)
        duration = QTableWidgetItem(duration)

        num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        artist.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        album.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        duration.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row_position, 0, num)
        self.setItem(row_position, 1, title)
        self.setItem(row_position, 2, artist)
        self.setItem(row_position, 3, album)
        self.setItem(row_position, 4, duration)

    def leaveEvent(self, event):
        self.clear_highlight()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        item = self.itemAt(event.pos())
        if item and item.row() != self.selected_row:
            row = item.row()
            if row != self.highlighted_row:
                self.clear_highlight()  # убираем подсветку предыдущей строки
                self.highlighted_row = row
                self.highlight_row(row, QColor(65, 65, 65, 70))  # подсвечиваем текущую строку
        else:
            self.clear_highlight()  # если мышь не над ячейкой, убираем подсветку
        super().mouseMoveEvent(event)

    def highlight_row(self, row, color):
        for column in range(self.columnCount()):
            item = self.item(row, column)
            if item:
                if row != self.selected_row:
                    item2 = self.item(row, 0)
                    item2.setText("")
                    item.setData(Qt.ItemDataRole.BackgroundRole, QBrush(QColor(color)))
                    button = InterfaceButton("resources\\icons\\play_icon_normal.png",
                                             "resources\\icons\\play_icon_hover.png",
                                             icon_size=16)
                    button.setStyleSheet("""
                                                QPushButton {
                                                    background-color: transparent;  /* Делаем фон прозрачным */
                                                    border: none;                   /* Убираем границу */
                                                }
                                            """)
                    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    button.clicked.connect(lambda x: self.play_track(item2.row(), button, self.widget))
                    if self.cur_track == row:
                        self.cur_button = button
                        if self.playing == QMediaPlayer.PlaybackState.PlayingState:
                            button.change_icon("resources\\icons\\pause_icon_normal.png",
                                               "resources\\icons\\pause_icon_hover.png")
                    self.setCellWidget(item.row(), 0, button)
                else:
                    item.setData(Qt.ItemDataRole.BackgroundRole, QBrush(QColor("#cdcdcd")))

    def play_track(self, row, button, widget):
        if self.cur_track != row:
            # Если текущий трек не равен выбранному, обновляем текущий трек
            self.cur_track = row
            self.select_row(row, 0)
        if self.playing == QMediaPlayer.PlaybackState.PlayingState:
            if button:
                button.change_icon("resources\\icons\\play_icon_normal.png", "resources\\icons\\play_icon_hover.png")
        else:
            if button:
                button.change_icon("resources\\icons\\pause_icon_normal.png", "resources\\icons\\pause_icon_hover.png")
        self.play_signal_table.emit(self.tracks_id[row], widget)

    def reset_cur_track(self):
        self.cur_track = -1

    def clear_highlight(self):
        if self.highlighted_row != -1:
            for column in range(self.columnCount()):
                item = self.item(self.highlighted_row, column)
                if item and item.row() != self.selected_row:
                    item.setBackground(QColor(0, 0, 0, 0))  # сбрасываем цвет фона
                    if column == 0:
                        self.removeCellWidget(self.highlighted_row, 0)
                        num = QTableWidgetItem(str(item.row() + 1))
                        num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.setItem(self.highlighted_row, 0, num)
            self.highlighted_row = -1

    def clear_selection(self):
        if self.selected_row != -1:
            for column in range(self.columnCount()):
                item = self.item(self.selected_row, column)
                if item:
                    item.setBackground(QColor(0, 0, 0, 0))  # сбрасываем цвет фона
                    if column == 0:
                        self.removeCellWidget(self.selected_row, 0)
                        num = QTableWidgetItem(str(item.row() + 1))
                        num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.setItem(self.selected_row, 0, num)
            self.selected_row = -1


class FavouritePlaylistTable(PlaylistTable):
    def __init__(self, user_id, parent=None):
        super().__init__(user_id, parent)
        self.set_widget(widget=1)
        self.start = 0

    def update_table(self):
        self.tracks_id = []
        self.setRowCount(0)
        favourite_tracks = client.get_favorite_tracks(self.user_id)
        self.tracks = favourite_tracks
        num = 1
        print(favourite_tracks)
        images = [[x[11]] for x in favourite_tracks]
        client.send_album_images(images)
        for track in favourite_tracks:
            self.tracks_id.append(track[0])
            seconds = round(track[5])
            duration = f"{seconds // 60}:{seconds % 60:02d}"
            self.add_track(str(num), track[1], track[7],
                           track[9], duration, "resources/" + track[11])
            self.setRowHeight(num - 1, 40)
            num += 1
        fnt = self.font()
        fnt.setPointSize(11)
        self.setFont(fnt)


class SearchPlaylistTable(PlaylistTable):
    def __init__(self, user_id, parent=None):
        super().__init__(user_id, parent)
        self.set_widget(widget=2)
        self.update_table()

    def update_table(self, title=None):
        # client.send_album_images()
        if title:
            self.tracks_id = []
            self.setRowCount(0)
            search_tracks = client.get_search_track(title)
            self.tracks = search_tracks
            num = 1
            for track in search_tracks:
                self.tracks_id.append(track[0])
                seconds = round(track[5])
                duration = f"{seconds // 60}:{seconds % 60:02d}"
                self.add_track(str(num), track[1], track[7],
                               track[9], duration, "resources/" + track[11])
                self.setRowHeight(num - 1, 40)
                num += 1
            fnt = self.font()
            fnt.setPointSize(11)
            self.setFont(fnt)


class AddTrackDialogUI(QDialog):
    def __init__(self):
        super().__init__()
        f = io.StringIO(template_add_track_dialog)
        uic.loadUi(f, self)


class FavouriteContentWidgetUI(QWidget):
    # класс окна (избранное в меню)
    def __init__(self, user_id):
        super().__init__()
        f = io.StringIO(template_favourite_content_widget)
        uic.loadUi(f, self)
        self.widget.setStyleSheet("background-color: transparent")
        self.line.setStyleSheet("background-color: rgba(255, 255, 10);")
        self.user_id = user_id
        self.initUI()

    def initUI(self):
        self.play_playlist_button = InterfaceButton("resources\\icons\\play_track_icon_normal",
                                                    "resources\\icons\\play_track_icon_normal",
                                                    self.play_playlist_button,
                                                    icon_size=85)
        self.playlist_table.setParent(None)
        self.playlist_table2 = FavouritePlaylistTable(self.user_id, parent=self.playlist_table)
        self.playlist_table2.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.playlist_table2.setMinimumHeight(10)
        self.verticalLayout.addWidget(self.playlist_table2)
        self.like_image.setStyleSheet("background-color: transparent")
        self.label.setStyleSheet("background-color: transparent")
        pixmap = QPixmap("resources\\icons\\star_favourite_icon.png")
        pixmap = pixmap.scaled(80, 80, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
        self.like_image.setPixmap(pixmap)


class SearchContentWidgetUI(QWidget):
    def __init__(self, user_id):
        super().__init__()
        f = io.StringIO(template_search_content_widget)
        uic.loadUi(f, self)
        self.info_label.setStyleSheet("background-color: transparent")
        self.search_image.setStyleSheet("background-color: transparent")
        self.label_3.setStyleSheet("background-color: transparent")
        self.line.setStyleSheet("background-color: rgba(255, 255, 10);")
        self.user_id = user_id
        self.initUI()

    def initUI(self):
        self.info_label.show()
        self.playlist_table.setParent(None)
        self.playlist_table3 = SearchPlaylistTable(self.user_id, parent=self.playlist_table)
        self.playlist_table3.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.playlist_table3.setMinimumHeight(10)
        self.verticalLayout.addWidget(self.playlist_table3)
        pixmap = QPixmap("resources\\icons\\search_icon.png")
        pixmap = pixmap.scaled(80, 80, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
        self.search_image.setPixmap(pixmap)


class MainFormUI(QMainWindow):
    def __init__(self, user_id=None):
        super().__init__()
        f = io.StringIO(template_main_form)
        uic.loadUi(f, self)
        self.user_id = user_id
        self.main_content_widget = MainContentWidgetUI(self.user_id)
        self.favourite_content_widget = FavouriteContentWidgetUI(self.user_id)
        self.search_content_widget = SearchContentWidgetUI(self.user_id)
        self.profile_content_widget = ProfileContentWidgetUI(self.user_id)
        self.setWindowIcon(QIcon("resources\\icons\\waveful_logo.png"))
        self.about_widget = AboutWidgetUI()
        self.initUI()
        self.show()

    def initUI(self):
        # создаем кнопки управления
        self.main_button = MenuListButton("Главное", "resources\\icons\\home_icon.png", 0)
        self.favourite_button = MenuListButton("Избранное", "resources\\icons\\star_icon.png", 1)
        self.search_track_button = MenuListButton("Поиск", "resources\\icons\\search_icon_filled.png", 2)
        self.profile_button = MenuListButton("Профиль", "resources\\icons\\profile_icon_filled.png", 3)

        # настраиваем меню и добавляем кнопки
        self.button_layout = QVBoxLayout()
        self.button_layout.setSpacing(8)
        self.button_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)
        self.menu_list.setLayout(self.button_layout)
        self.menu_list.setStyleSheet("background-color: transparent")
        self.button_layout.addWidget(self.main_button)
        self.button_layout.addWidget(self.favourite_button)
        self.button_layout.addWidget(self.search_track_button)
        self.button_layout.addWidget(self.profile_button)
        # используем stacked_widget для отображения основных страниц
        self.stacked_widget = QStackedWidget(self)
        self.scroll_content.setWidgetResizable(True)
        self.scroll_content.setWidget(self.stacked_widget)
        # добавляем основные страницы
        self.stacked_widget.addWidget(self.main_content_widget)
        self.stacked_widget.addWidget(self.favourite_content_widget)
        self.stacked_widget.addWidget(self.search_content_widget)
        self.stacked_widget.addWidget(self.profile_content_widget)
        # настраиваем статус-бар
        self.status_bar = PlayStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.status_widget.image_label.mousePressEvent = self.show_large_image
        # настраиваем виджет поиска
        self.widget.setStyleSheet("background-color: #101010")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border-radius: 20px;
                background-color: #363636;
                padding: 10px;           /* Отступы внутри поля */
            }
            QLineEdit:focus {
                border: 2px solid #01B8C2; /* Цвет рамки при фокусе */
            }
            QLineEdit:hover {
                background-color: #4d4d4d;
            }
        """)
        self.search_button.setStyleSheet("""
            QPushButton {
                border-radius: 22px;
                background-color: #363636;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)
        self.search_button.setIcon(QIcon("resources\\icons\\search_music.png"))
        self.search_button.setIconSize(QSize(35, 35))
        # настройка кнопки обновления
        self.update_button.setStyleSheet("""
            QPushButton {
                color: white;
                border-radius: 15px;
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 0, 0, 255), stop:1 rgba(255, 100, 245, 255));
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(spread:pad, x1:1, y1:0, x2:0, y2:0, stop:0 rgba(255, 0, 0, 255), stop:1 rgba(255, 100, 245, 255));
            }
        """)
        self.update_button.hide()
        # настройка меню QToolButton
        self.menu_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu_button.setIcon(QIcon("resources\\icons\\menu_icon.png"))
        self.menu_button.setIconSize(QSize(100, 100))
        self.menu = QMenu()
        self.action1 = self.menu.addAction("О waveful")
        self.action1.triggered.connect(lambda: self.option_selected(0))
        self.menu_button.setMenu(self.menu)

        self.overlay = QWidget(self)
        self.overlay.setGeometry(self.rect())
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        self.overlay.mousePressEvent = lambda event: self.close_overlay(self.overlay)
        self.large_image_label = QLabel(self.overlay)

        self.large_image_label.setMinimumSize(100, 100)
        self.large_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_pixmap = QPixmap(self.status_bar.current_album)

        self.opacity_effect = QGraphicsOpacityEffect(self.overlay)
        self.overlay.setGraphicsEffect(self.opacity_effect)

        self.overlay_animation_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.overlay_animation_in.setDuration(500)
        self.overlay_animation_in.setStartValue(0.0)
        self.overlay_animation_in.setEndValue(1.0)

        self.overlay_animation_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.overlay_animation_out.setDuration(300)
        self.overlay_animation_out.setStartValue(1.0)
        self.overlay_animation_out.setEndValue(0.0)

        self.large_image_label.hide()
        self.overlay.hide()

        self.fullscreen_overlay = QWidget(self)
        f = io.StringIO(template_fullscreen_widget)
        uic.loadUi(f, self.fullscreen_overlay)
        self.fullscreen_overlay.setGeometry(self.rect())
        # self.fullscreen_overlay.album_image.setPixmap(QPixmap(self.status_bar.current_album))

        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)
        self.fullscreen_overlay.title_label.setFont(title_font)

        artist_font = QFont()
        artist_font.setBold(True)
        artist_font.setPointSize(12)
        self.fullscreen_overlay.artist_label.setFont(artist_font)

        self.fullscreen_overlay.close_button = InterfaceButton("resources/icons/close_fullscreen_icon_normal.png",
                                                               "resources/icons/close_fullscreen_icon_hover.png",
                                                               self.fullscreen_overlay.close_button,
                                                               icon_size=40)
        self.fullscreen_overlay.shuffle_button = InterfaceButton("resources/icons/shuffle_icon_normal.png",
                                                                 "resources/icons/shuffle_icon_hover.png",
                                                                 self.fullscreen_overlay.shuffle_button, icon_size=24)
        self.fullscreen_overlay.next_button = InterfaceButton("resources/icons/next_icon_normal.png",
                                                              "resources/icons/next_icon_hover.png",
                                                              self.fullscreen_overlay.next_button, icon_size=24)
        self.fullscreen_overlay.repeat_button = InterfaceButton("resources/icons/repeat_icon_normal.png",
                                                                "resources/icons/repeat_icon_hover.png",
                                                                self.fullscreen_overlay.repeat_button, icon_size=24)
        self.fullscreen_overlay.previous_button = InterfaceButton("resources/icons/previous_icon_normal.png",
                                                                  "resources/icons/previous_icon_hover.png",
                                                                  self.fullscreen_overlay.previous_button,
                                                                  icon_size=24)
        self.fullscreen_overlay.play_button = InterfaceButton("resources/icons/play_track_icon_normal.png",
                                                              "resources/icons/play_track_icon_normal.png",
                                                              self.fullscreen_overlay.play_button,
                                                              icon_size=40)

        self.fullscreen_overlay.close_button.clicked.connect(
            lambda _: self.close_fullscreen_overlay(self.fullscreen_overlay))
        self.background_color = (0, 0, 0)
        # self.shadow_effect = QGraphicsDropShadowEffect()
        # self.shadow_effect.setBlurRadius(50)
        # self.shadow_effect.setXOffset(0)
        # self.shadow_effect.setYOffset(0)
        # self.shadow_effect.setColor(QColor(0, 0, 0, 160))
        self.fullscreen_overlay.setStyleSheet(
            f"background-color: rgb{self.background_color};")

        self.animated_bars = [self.fullscreen_overlay.frame, self.fullscreen_overlay.frame_2,
                              self.fullscreen_overlay.frame_3, self.fullscreen_overlay.frame_4,
                              self.fullscreen_overlay.frame_5, self.fullscreen_overlay.frame_6,
                              self.fullscreen_overlay.frame_7, self.fullscreen_overlay.frame_8]

        self.animations = []

        for bar in self.animated_bars:
            bar.setMaximumSize(25, round(self.size().height() * 0.5))

        self.opacity_effect2 = QGraphicsOpacityEffect()
        self.opacity_effect2.setOpacity(1.0)
        self.fullscreen_overlay.setGraphicsEffect(self.opacity_effect2)

        self.fullscreen_overlay_animation_in = QPropertyAnimation(self.opacity_effect2, b"opacity")
        self.fullscreen_overlay_animation_in.setDuration(500)
        self.fullscreen_overlay_animation_in.setStartValue(0.0)
        self.fullscreen_overlay_animation_in.setEndValue(1.0)

        self.fullscreen_overlay_animation_out = QPropertyAnimation(self.opacity_effect2, b"opacity")
        self.fullscreen_overlay_animation_out.setDuration(300)
        self.fullscreen_overlay_animation_out.setStartValue(1.0)
        self.fullscreen_overlay_animation_out.setEndValue(0.0)

        self.bar_animation1_in = QPropertyAnimation(self.fullscreen_overlay.frame, b"maximumSize")
        self.bar_animation1_in.setDuration(400)
        self.bar_animation1_in.setStartValue(QSize(25, round(self.size().height() * 0.3)))
        self.bar_animation1_in.setEndValue(QSize(25, round(self.size().height() * 0.5)))
        self.bar_animation1_in.setEasingCurve(QtCore.QEasingCurve.Type.InBounce)
        self.animations.append(self.bar_animation1_in)

        self.bar_animation1_out = QPropertyAnimation(self.fullscreen_overlay.frame, b"maximumSize")
        self.bar_animation1_out.setDuration(400)
        self.bar_animation1_out.setStartValue(QSize(25, round(self.size().height() * 0.5)))
        self.bar_animation1_out.setEndValue(QSize(25, round(self.size().height() * 0.3)))
        self.bar_animation1_out.setEasingCurve(QtCore.QEasingCurve.Type.InBounce)
        self.animations.append(self.bar_animation1_out)

        self.bar_animation2_in = QPropertyAnimation(self.fullscreen_overlay.frame_2, b"maximumSize")
        self.bar_animation2_in.setDuration(400)
        self.bar_animation2_in.setStartValue(QSize(25, round(self.size().height() * 0.4)))
        self.bar_animation2_in.setEndValue(QSize(25, round(self.size().height() * 0.1)))
        self.bar_animation2_in.setEasingCurve(QtCore.QEasingCurve.Type.InBounce)
        self.animations.append(self.bar_animation2_in)

        self.bar_animation2_out = QPropertyAnimation(self.fullscreen_overlay.frame_2, b"maximumSize")
        self.bar_animation2_out.setDuration(400)
        self.bar_animation2_out.setStartValue(QSize(25, round(self.size().height() * 0.1)))
        self.bar_animation2_out.setEndValue(QSize(25, round(self.size().height() * 0.4)))
        self.bar_animation2_out.setEasingCurve(QtCore.QEasingCurve.Type.InBounce)
        self.animations.append(self.bar_animation2_out)

        self.bar_animation3_in = QPropertyAnimation(self.fullscreen_overlay.frame_3, b"maximumSize")
        self.bar_animation3_in.setDuration(350)
        self.bar_animation3_in.setStartValue(QSize(25, round(self.size().height() * 0.2)))
        self.bar_animation3_in.setEndValue(QSize(25, round(self.size().height() * 0.4)))
        self.bar_animation3_in.setEasingCurve(QtCore.QEasingCurve.Type.InBounce)
        self.animations.append(self.bar_animation3_in)

        self.bar_animation3_out = QPropertyAnimation(self.fullscreen_overlay.frame_3, b"maximumSize")
        self.bar_animation3_out.setDuration(350)
        self.bar_animation3_out.setStartValue(QSize(25, round(self.size().height() * 0.4)))
        self.bar_animation3_out.setEndValue(QSize(25, round(self.size().height() * 0.2)))
        self.bar_animation3_out.setEasingCurve(QtCore.QEasingCurve.Type.InBounce)
        self.animations.append(self.bar_animation3_out)

        self.bar_animation4_in = QPropertyAnimation(self.fullscreen_overlay.frame_4, b"maximumSize")
        self.bar_animation4_in.setDuration(350)
        self.bar_animation4_in.setStartValue(QSize(25, round(self.size().height() * 0.5)))
        self.bar_animation4_in.setEndValue(QSize(25, round(self.size().height() * 0.2)))
        self.bar_animation4_in.setEasingCurve(QtCore.QEasingCurve.Type.InBounce)
        self.animations.append(self.bar_animation4_in)

        self.bar_animation4_out = QPropertyAnimation(self.fullscreen_overlay.frame_4, b"maximumSize")
        self.bar_animation4_out.setDuration(350)
        self.bar_animation4_out.setStartValue(QSize(25, round(self.size().height() * 0.2)))
        self.bar_animation4_out.setEndValue(QSize(25, round(self.size().height() * 0.5)))
        self.bar_animation4_out.setEasingCurve(QtCore.QEasingCurve.Type.InBounce)
        self.animations.append(self.bar_animation4_out)

        self.bar_animation5_in = QPropertyAnimation(self.fullscreen_overlay.frame_5, b"maximumSize")
        self.bar_animation5_in.setDuration(350)
        self.bar_animation5_in.setStartValue(QSize(25, round(self.size().height() * 0.2)))
        self.bar_animation5_in.setEndValue(QSize(25, round(self.size().height() * 0.4)))
        self.bar_animation5_in.setEasingCurve(QtCore.QEasingCurve.Type.InBounce)
        self.animations.append(self.bar_animation5_in)

        self.bar_animation5_out = QPropertyAnimation(self.fullscreen_overlay.frame_5, b"maximumSize")
        self.bar_animation5_out.setDuration(350)
        self.bar_animation5_out.setStartValue(QSize(25, round(self.size().height() * 0.4)))
        self.bar_animation5_out.setEndValue(QSize(25, round(self.size().height() * 0.2)))
        self.bar_animation5_out.setEasingCurve(QtCore.QEasingCurve.Type.InBounce)
        self.animations.append(self.bar_animation5_out)

        self.bar_animation6_in = QPropertyAnimation(self.fullscreen_overlay.frame_6, b"maximumSize")
        self.bar_animation6_in.setDuration(400)
        self.bar_animation6_in.setStartValue(QSize(25, round(self.size().height() * 0.3)))
        self.bar_animation6_in.setEndValue(QSize(25, round(self.size().height() * 0.5)))
        self.bar_animation6_in.setEasingCurve(QtCore.QEasingCurve.Type.InBounce)
        self.animations.append(self.bar_animation6_in)

        self.bar_animation6_out = QPropertyAnimation(self.fullscreen_overlay.frame_6, b"maximumSize")
        self.bar_animation6_out.setDuration(400)
        self.bar_animation6_out.setStartValue(QSize(25, round(self.size().height() * 0.5)))
        self.bar_animation6_out.setEndValue(QSize(25, round(self.size().height() * 0.3)))
        self.bar_animation6_out.setEasingCurve(QtCore.QEasingCurve.Type.InBounce)
        self.animations.append(self.bar_animation6_out)

        self.bar_animation7_in = QPropertyAnimation(self.fullscreen_overlay.frame_7, b"maximumSize")
        self.bar_animation7_in.setDuration(350)
        self.bar_animation7_in.setStartValue(QSize(25, round(self.size().height() * 0.2)))
        self.bar_animation7_in.setEndValue(QSize(25, round(self.size().height() * 0.4)))
        self.bar_animation7_in.setEasingCurve(QtCore.QEasingCurve.Type.InBounce)
        self.animations.append(self.bar_animation7_in)

        self.bar_animation7_out = QPropertyAnimation(self.fullscreen_overlay.frame_7, b"maximumSize")
        self.bar_animation7_out.setDuration(350)
        self.bar_animation7_out.setStartValue(QSize(25, round(self.size().height() * 0.4)))
        self.bar_animation7_out.setEndValue(QSize(25, round(self.size().height() * 0.2)))
        self.bar_animation7_out.setEasingCurve(QtCore.QEasingCurve.Type.InBounce)
        self.animations.append(self.bar_animation7_out)

        self.bar_animation8_in = QPropertyAnimation(self.fullscreen_overlay.frame_8, b"maximumSize")
        self.bar_animation8_in.setDuration(400)
        self.bar_animation8_in.setStartValue(QSize(25, round(self.size().height() * 0.1)))
        self.bar_animation8_in.setEndValue(QSize(25, round(self.size().height() * 0.3)))
        self.bar_animation8_in.setEasingCurve(QtCore.QEasingCurve.Type.InBounce)
        self.animations.append(self.bar_animation8_in)

        self.bar_animation8_out = QPropertyAnimation(self.fullscreen_overlay.frame_8, b"maximumSize")
        self.bar_animation8_out.setDuration(400)
        self.bar_animation8_out.setStartValue(QSize(25, round(self.size().height() * 0.3)))
        self.bar_animation8_out.setEndValue(QSize(25, round(self.size().height() * 0.1)))
        self.bar_animation8_out.setEasingCurve(QtCore.QEasingCurve.Type.InBounce)
        self.animations.append(self.bar_animation8_out)


        for index, anim in enumerate(self.animations):
            anim.finished.connect(lambda ind=index: self.on_animation_finished(ind))

        self.fullscreen_overlay.hide()

    def start_color_animation(self, prev_color):
        self.color_animation = QPropertyAnimation(self, b"color")
        self.color_animation.setDuration(1000)
        self.color_animation.setStartValue(QColor(round(prev_color[0]), round(prev_color[1]), round(prev_color[2])))
        self.color_animation.setEndValue(QColor(round(self.background_color[0]), round(self.background_color[1]), round(self.background_color[2])))
        self.color_animation.setEasingCurve(QtCore.QEasingCurve.Type.InQuad)
        self.color_animation.valueChanged.connect(self.update_color)
        self.color_animation.start()

    def update_color(self, color):
        self.fullscreen_overlay.setStyleSheet(f"background-color: rgb({color.red()}, {color.green()}, {color.blue()});")

    def init_animation(self, animation, bar):
        animation.setDuration(300)
        animation.setStartValue(QSize(25, bar.height()))
        animation.setEndValue(QSize(25, 0))
        return animation

    def pause_visualizer(self):
        self.hide_animations = [self.init_animation(QPropertyAnimation(bar, b"maximumSize"), bar) for bar in
                                self.animated_bars]
        for anim in self.hide_animations:
            anim.start()

    def on_animation_finished(self, index):
        print(index)
        if index % 2 == 0:
            pair_animation = self.animations[index + 1]
        else:
            pair_animation = self.animations[index - 1]
        pair_animation.start()

    def resizeEvent(self, event):
        print(f"Размер окна изменен: {self.size()}")
        self.change_overlay_size()
        self.change_fullscreen_overlay_size()
        super().resizeEvent(event)  # Вызов родительского метод

    def display_track(self):
        self.original_pixmap = QPixmap(self.status_bar.current_album)
        previous_color = self.background_color
        self.background_color = client.find_average_color(self.status_bar.current_album)
        self.start_color_animation(previous_color)
        size = self.size()
        self.fullscreen_overlay.resize(size)
        width = round(size.width() * 0.65)
        height = round(size.height() * 0.65)
        pixmap = self.original_pixmap.scaled(width, height,
                                             Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
        self.fullscreen_overlay.album_image.setPixmap(pixmap)
        self.fullscreen_overlay.title_label.setText(self.status_bar.status_widget.track_label.text())
        self.fullscreen_overlay.artist_label.setText(self.status_bar.status_widget.artist_label.text())
        self.fullscreen_overlay.current_label.setText(self.status_bar.status_widget.current_label.text())
        self.fullscreen_overlay.duration_label.setText(self.status_bar.status_widget.duration_label.text())

    def show_large_image(self, event):
        self.original_pixmap = QPixmap(self.status_bar.current_album)
        size = self.size()
        pixmap = self.original_pixmap.scaled(round(size.width() * 0.75), round(size.height() * 0.75),
                                             Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
        self.large_image_label.setPixmap(pixmap)
        self.large_image_label.setGeometry(self.rect())
        self.large_image_label.show()
        self.overlay.show()

        self.overlay_animation_in.start()

    def start_visualizer(self):
        self.bar_animation1_in.start()
        self.bar_animation2_in.start()
        self.bar_animation3_in.start()
        self.bar_animation4_in.start()
        self.bar_animation5_in.start()
        self.bar_animation6_in.start()
        self.bar_animation7_in.start()
        self.bar_animation8_in.start()

    def show_fullscreen_overlay(self, playing=True):
        self.original_pixmap = QPixmap(self.status_bar.current_album)
        print(self.original_pixmap)
        self.display_track()
        self.fullscreen_overlay.show()
        self.fullscreen_overlay_animation_in.start()
        if playing:
            self.start_visualizer()

    def close_fullscreen_overlay(self, overlay):
        timer = QTimer(self)
        timer.setSingleShot(True)
        self.fullscreen_overlay_animation_out.start()
        timer.start(300)
        timer.timeout.connect(overlay.hide)
        for animation in self.animations:
            animation.stop()

    def close_overlay(self, overlay):
        timer = QTimer(self)
        timer.setSingleShot(True)
        self.overlay_animation_out.start()
        timer.start(300)
        timer.timeout.connect(overlay.hide)

    def change_fullscreen_overlay_size(self):
        size = self.size()
        self.fullscreen_overlay.resize(size)
        width = round(size.width() * 0.65)
        height = round(size.height() * 0.65)
        pixmap = self.original_pixmap.scaled(width, height,
                                             Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
        self.fullscreen_overlay.album_image.setMaximumSize(pixmap.size())
        self.fullscreen_overlay.track_slider.setFixedWidth(round(pixmap.width() * 0.75))
        print(pixmap.width())
        self.fullscreen_overlay.album_image.setPixmap(pixmap)

    def change_overlay_size(self):
        size = self.size()
        self.overlay.resize(size)
        self.large_image_label.resize(size)
        pixmap = self.original_pixmap.scaled(round(size.width() * 0.75), round(size.height() * 0.75),
                                             Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
        self.large_image_label.setPixmap(pixmap)
        print(self.size())

    def option_selected(self, index):
        if index == 0:
            self.about_widget.show()


class StatusBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        f = io.StringIO(template_status_bar)
        uic.loadUi(f, self)
        font = QFont()
        font.setPointSize(12)
        self.track_label.setFont(font)
        self.artist_label.setStyleSheet("color: lightgray;")
        self.volume_slider.setStyleSheet("""QSlider::groove:horizontal {
    border-radius: 8px;       
    height: 6px;
    margin: -1px 0;         
       
}
QSlider::handle:horizontal {
    background-color: #1de1da;
    border: 1px solid #313431;
    height: 12px;     
    width: 12px;   
    border-radius: 7px;
    margin: -4px 0;   
    padding: -4px 0px;  
}
QSlider::add-page:horizontal {
    background: #9b9b9b;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 0, 0, 255), stop:1 rgba(255, 100, 245, 255));
}""")
        self.track_slider.setStyleSheet("""QSlider::groove:horizontal {
    border-radius: 1px;       
    height: 6px;              
    margin: -1px 0;           
}
QSlider::handle:horizontal {
    background-color: #1de1da;
    border: 1px solid #313431;
    height: 12px;     
    width: 12px;
    margin: -4px 0;     
    border-radius: 7px  ;
    padding: -4px 0px;  
}
QSlider::add-page:horizontal {
    background: #9b9b9b;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 0, 0, 255), stop:1 rgba(255, 100, 245, 255));
}""")
        self.hide()


class PlayStatusBar(QStatusBar):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(960, 80)
        self.current_album = "resources/waveful_logo.ico"
        self.status_widget = StatusBarWidget(self)
        self.addWidget(self.status_widget)
        self.setSizeGripEnabled(False)
        self.setStyleSheet("background-color: #101010")
        self.add_favourite_button = InterfaceButton("resources\\icons\\like_icon_normal.png",
                                                    "resources\\icons\\like_icon_hover.png",
                                                    self.status_widget.add_favourite_button, icon_size=20)
        self.shuffle_button = InterfaceButton("resources\\icons\\shuffle_icon_normal.png",
                                              "resources\\icons\\shuffle_icon_hover.png",
                                              self.status_widget.shuffle_button, icon_size=24)
        self.next_button = InterfaceButton("resources\\icons\\next_icon_normal.png",
                                           "resources\\icons\\next_icon_hover.png",
                                           self.status_widget.next_button, icon_size=24)
        self.repeat_button = InterfaceButton("resources\\icons\\repeat_icon_normal.png",
                                             "resources\\icons\\repeat_icon_hover.png",
                                             self.status_widget.repeat_button, icon_size=24)
        self.previous_button = InterfaceButton("resources\\icons\\previous_icon_normal.png",
                                               "resources\\icons\\previous_icon_hover.png",
                                               self.status_widget.previous_button,
                                               icon_size=24)
        self.play_button = InterfaceButton("resources\\icons\\play_track_icon_normal.png",
                                           "resources\\icons\\play_track_icon_normal.png",
                                           self.status_widget.play_button,
                                           icon_size=40)
        self.mute_button = InterfaceButton("resources\\icons\\volume_medium_icon_normal.png",
                                           "resources\\icons\\volume_medium_icon_hover.png",
                                           self.status_widget.mute_button,
                                           icon_size=24)
        self.maximize_button = InterfaceButton("resources\\icons\\maximize_icon_normal.png",
                                               "resources\\icons\\maximize_icon_hover.png",
                                               self.status_widget.maximize_button, icon_size=24)

    # метод для отображения всей информации о текущем треке
    def display(self, title, artist, album_path, duration, track_id, session):
        self.status_widget.show()
        self.current_album = f"resources/{album_path}"
        icon = QIcon("resources/" + album_path)
        pixmap = icon.pixmap(64, 64)
        self.status_widget.track_label.setText(title)
        self.status_widget.artist_label.setText(artist)
        self.status_widget.image_label.setPixmap(pixmap)
        self.status_widget.duration_label.setText(duration)
        self.status_widget.current_label.setText("0:00")
        self.status_widget.track_slider.setValue(0)
        if client.get_favorite_track(session, track_id):
            self.add_favourite_button.change_icon("resources\\icons\\liked_icon.png",
                                                  "resources\\icons\\liked_icon.png")
        else:
            self.add_favourite_button.change_icon("resources\\icons\\like_icon_normal.png",
                                                  "resources\\icons\\like_icon_hover.png")

    # меняем иконку в зависимости от громкости
    def change_volume_icon(self, volume):
        if volume == 0:
            self.mute_button.change_icon("resources\\icons\\volume_mute_icon_normal.png",
                                         "resources\\icons\\volume_mute_icon_hover.png")
        elif 0 < volume < 33:
            self.mute_button.change_icon("resources\\icons\\volume_low_icon_normal.png",
                                         "resources\\icons\\volume_low_icon_hover.png")
        elif 33 <= volume < 67:
            self.mute_button.change_icon("resources\\icons\\volume_medium_icon_normal.png",
                                         "resources\\icons\\volume_medium_icon_hover.png")
        elif 67 <= volume < 100:
            self.mute_button.change_icon("resources\\icons\\volume_high_icon_normal.png",
                                         "resources\\icons\\volume_high_icon_hover.png")


class MainContentWidgetUI(QWidget):
    # класс окна (главное в меню)
    def __init__(self, user_id):
        super().__init__()
        f = io.StringIO(template_main_content_widget)
        uic.loadUi(f, self)
        self.button_widget.setStyleSheet("background-color: transparent")
        self.label.setStyleSheet("background-color: transparent")
        self.crown_image.setStyleSheet("background-color: transparent")
        self.line.setStyleSheet("background-color: rgba(255, 255, 10);")
        self.user_id = user_id
        self.initUI()

    def initUI(self):
        pixmap = QPixmap("resources\\icons\\crown_icon")
        pixmap = pixmap.scaled(100, 100, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
        self.crown_image.setPixmap(pixmap)
        self.verticalLayout.addStretch()
        self.upload_track_button = InterfaceButton("resources\\icons\\upload_icon_normal.png",
                                                   "resources\\icons\\upload_icon_hover.png", self.upload_track_button)
        self.reload_table_button = InterfaceButton("resources\\icons\\reload_icon_normal.png",
                                                   "resources\\icons\\reload_icon_hover.png", self.reload_table_button)
        self.play_playlist_button = InterfaceButton("resources\\icons\\play_track_icon_normal",
                                                    "resources\\icons\\play_track_icon_normal",
                                                    self.play_playlist_button,
                                                    icon_size=85)
        self.playlist_table.setParent(None)
        self.playlist_table1 = PlaylistTable(self.user_id, self.playlist_table)
        self.playlist_table1.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.playlist_table1.setMinimumHeight(10)
        self.verticalLayout.addWidget(self.playlist_table1)
        self.reload_table_button.clicked.connect(self.playlist_table1.update_table)


class ProfileContentWidgetUI(QWidget):
    def __init__(self, user_id):
        super().__init__()
        f = io.StringIO(template_profile_content_widget)
        uic.loadUi(f, self)
        self.label_2.setStyleSheet("background-color: transparent")
        self.label.setStyleSheet("background-color: transparent")
        self.login.setStyleSheet("background-color: transparent")
        self.password.setStyleSheet("background-color: transparent")
        self.label_4.setStyleSheet("background-color: transparent")
        self.change_password.setStyleSheet("background-color: transparent")
        self.new_password_input.setStyleSheet("background-color: transparent")
        self.confirm_button.setStyleSheet("background-color: #26c9a8")
        self.exit_button.setStyleSheet("background-color: red")
        self.line.setStyleSheet("background-color: rgba(255, 255, 10);")
        self.user_id = user_id
        self.show_pass = True
        self.new_password_input.hide()
        self.confirm_button.hide()
        self.initUI()
        self.set_login_password()

    def initUI(self):
        self.see_password = InterfaceButton("resources\\icons\\eye_enable_icon_normal.png",
                                            "resources\\icons\\eye_enable_icon_hover.png", self.see_password,
                                            icon_size=24)
        self.see_password.clicked.connect(self.show_password)
        self.change_password.stateChanged.connect(self.show_fields)
        self.confirm_button.clicked.connect(self.change_user_password)
        pixmap = QPixmap("resources\\icons\\profile_icon.png")
        pixmap = pixmap.scaled(80, 80, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
        self.profile_image.setStyleSheet("background-color: transparent")
        self.profile_image.setPixmap(pixmap)

    def change_user_password(self):
        new_password = self.new_password_input.text()
        if new_password:
            client.change_user_password(self.user_id, new_password)
        self.set_login_password()
        self.show_pass = True

    def show_fields(self):
        if not self.change_password.isChecked():
            self.new_password_input.hide()
            self.confirm_button.hide()
        else:
            self.new_password_input.show()
            self.confirm_button.show()

    def show_password(self):
        if self.show_pass == True:
            self.see_password.change_icon("resources\\icons\\eye_disable_icon_normal.png",
                                          "resources\\icons\\eye_disable_icon_hover.png")
            self.password.setText(self.user[1])
            self.show_pass = False
        else:
            self.see_password.change_icon("resources\\icons\\eye_enable_icon_normal.png",
                                          "resources\\icons\\eye_enable_icon_hover.png")
            self.password.setText("**********")
            self.show_pass = True

    def set_login_password(self):
        self.user = client.get_user_by_id(self.user_id)
        self.login.setText(self.user[0])
        self.password.setText("**********")


class AboutWidgetUI(QWidget):
    def __init__(self):
        super().__init__()
        f = io.StringIO(template_about_widget)
        uic.loadUi(f, self)
        pixmap = QPixmap("resources\\icons\\waveful_logo.png")
        scaled_pixmap = pixmap.scaled(100, 100)
        self.logo_label.setPixmap(scaled_pixmap)
        self.logo_label.resize(pixmap.width(), pixmap.height())


class LoginFormUI(QWidget):
    def __init__(self):
        super().__init__()
        f = io.StringIO(template_login_form)
        uic.loadUi(f, self)
        self.setWindowIcon(QIcon("resources\\icons\\waveful_logo.png"))
        self.initUI()

    def initUI(self):
        # надпись для ошибок и удачной регистрации
        self.message_label.hide()
        # надписи к полям
        self.login_input.setPlaceholderText("Login")
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        # текст-гиперссылка для регистрации
        self.register_hypertext.setStyleSheet("color: RoyalBlue; text-decoration: underline;")
        self.register_hypertext.setCursor(Qt.CursorShape.PointingHandCursor)
        self.register_hypertext.mousePressEvent = self.on_label_click

        # устанавливаем фильтр событий, чтобы при получении FocusIn ивента вызвать только 1 функцию и не терять курсор
        self.password_input.installEventFilter(self)
        self.login_input.installEventFilter(self)

    def on_label_click(self, event):
        pass

    def set_message_label(self, text, color):
        self.message_label.setText(text)
        self.message_label.setStyleSheet(f"color: {color};")
        self.message_label.show()

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.FocusIn:
            if source in (self.login_input, self.password_input):
                self.clear_error_fields()
        return super().eventFilter(source, event)

    def clear_error_fields(self):
        # очищение полей при новом вводе
        if self.message_label.text() == "Неверный логин или пароль" or self.message_label.text() == "Ошибка ввода":
            self.login_input.setStyleSheet("")
            self.password_input.setStyleSheet("")
            self.login_input.setText("")
            self.password_input.setText("")
            self.message_label.setText("")

    def highlight_fields(self):
        # подсветка полей с ошибкой
        self.login_input.setStyleSheet("border: 1px solid red;")
        self.password_input.setStyleSheet("border: 1px solid red;")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LoginFormUI()
    ex.show()
    sys.exit(app.exec())
