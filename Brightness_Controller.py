import sys
import os
import screen_brightness_control as sbc
from win32com.client import Dispatch
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QMainWindow, QSystemTrayIcon
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QFont


def emoji_icon(emoji="☀️", size=64):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setFont(QFont("Segoe UI Emoji", int(size * 0.6)))
    painter.setPen(Qt.black)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, emoji)
    painter.end()
    return QIcon(pixmap)


class BrightnessApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_window()
        self.setup_tray_icon()
        self.init_ui()

    def setup_window(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            background-color: #2d2d2d;
            color: white;
            font-size: 14px;
            border-radius: 10px;
        """)
        self.setGeometry(300, 300, 350, 80)
        self.setWindowIcon(emoji_icon("☀️"))
        self.old_pos = None

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(emoji_icon("☀️"), self)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        self.monitors = sbc.list_monitors()

        brightness = self.get_current_brightness()

        icon = QLabel("☀️", self)
        icon.setFixedWidth(30)
        icon.setAlignment(Qt.AlignCenter)

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(brightness)
        self.slider.setFixedHeight(18)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(20)
        self.slider.valueChanged.connect(self.on_slider_change)
        self.style_slider()

        self.value_label = QLabel(f"{brightness}%", self)
        self.value_label.setFixedWidth(40)
        self.value_label.setAlignment(Qt.AlignCenter)

        slider_row = QHBoxLayout()
        slider_row.addWidget(icon)
        slider_row.addWidget(self.slider)
        slider_row.addWidget(self.value_label)

        main_layout.addLayout(slider_row)

    def get_current_brightness(self):
        try:
            return sbc.get_brightness(display=0)[0]
        except Exception:
            return 50

    def style_slider(self):
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #555; border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #1a73e8; border-radius: 2px; }
            QSlider::handle:horizontal { background: white; width: 18px; height: 18px; margin: -8px 0; border-radius: 9px; }
            QSlider::tick-position:below { background: #aaa; }
        """)

    def on_slider_change(self, value):
        self.value_label.setText(f"{value}%")
        self.update_brightness(value)

    def update_brightness(self, value):
        try:
            for idx in range(len(self.monitors)):
                sbc.set_brightness(value, display=idx)
        except Exception as e:
            print(f"Error setting brightness: {e}")

    def set_profile_brightness(self, value):
        self.slider.setValue(value)
        self.on_slider_change(value)

    def show_window(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x = screen_geometry.right() - self.width() - 10
        y = screen_geometry.bottom() - self.height() - 10
        self.move(x, y)
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show_window()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def focusOutEvent(self, event):
        self.hide()

    def event(self, event):
        if event.type() == event.WindowDeactivate:
            self.hide()
        return super().event(event)


def enable_autostart():
    startup_dir = os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
    script_path = os.path.abspath(sys.argv[0])
    shortcut_path = os.path.join(startup_dir, 'BrightnessController.lnk')

    if not os.path.exists(shortcut_path):
        try:
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = script_path.replace('.py', '.exe') if script_path.endswith('.py') else script_path
            shortcut.WorkingDirectory = os.path.dirname(script_path)
            shortcut.IconLocation = script_path
            shortcut.save()
        except Exception as e:
            print(f"Could not create startup shortcut: {e}")


def main():
    app = QApplication(sys.argv)
    enable_autostart()
    window = BrightnessApp()
    window.hide()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
