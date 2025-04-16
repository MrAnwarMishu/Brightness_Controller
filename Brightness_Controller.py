import sys
import os
import screen_brightness_control as sbc
import winreg
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QSlider, QHBoxLayout, QVBoxLayout,
    QMainWindow, QSystemTrayIcon, QMenu, QAction
)
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QRect, QEasingCurve
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QFont


def emoji_icon(emoji="☀️", size=64):
    """Generate a crisp emoji icon for system tray use."""
    scale = QApplication.primaryScreen().devicePixelRatio()  # Get screen scale factor
    base_size = int(size * scale)  # Adjust size based on DPI scaling

    pixmap = QPixmap(base_size, base_size)
    pixmap.setDevicePixelRatio(scale)  # Ensure it scales properly for high-DPI displays
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    font = QFont("Segoe UI Emoji", int(base_size * 0.6))
    font.setStyleStrategy(QFont.PreferAntialias)
    painter.setFont(font)
    painter.setPen(Qt.black)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, emoji)
    painter.end()

    return QIcon(pixmap)


def get_icon_by_brightness(value):
    """Return different icon based on brightness level."""
    if value <= 25:
        return emoji_icon("🌑")  # Dark
    elif value <= 75:
        return emoji_icon("🌤️")  # Partly cloudy
    else:
        return emoji_icon("☀️")  # Bright Sun


class BrightnessApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_window()
        self.setup_tray_icon()
        self.init_ui()

    def setup_window(self):
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("""
            background-color: #2d2d2d;
            color: white;
            font-size: 14px;
            border-radius: 10px;
        """)
        self.setGeometry(300, 300, 350, 80)
        self.old_pos = None

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(emoji_icon("☀️"), self)

        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #444;
                padding: 4px;
                font-size: 13px;
            }
            QMenu::item {
                padding: 6px 20px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #1a73e8;
            }
        """)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

        # Set the tooltip to show brightness percentage
        self.tray_icon.setToolTip(f"Brightness: {self.get_current_brightness()}%")

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

        # Update tooltip with the current brightness percentage
        self.tray_icon.setToolTip(f"Brightness: {value}%")

        # Update the tray icon based on brightness level
        self.tray_icon.setIcon(get_icon_by_brightness(value))

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

        # Create QPropertyAnimation for the window position (from below screen)
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(500)  # Reduced duration to make it faster
        self.animation.setStartValue(QPoint(self.x(), screen_geometry.bottom()))  # Start from bottom of screen
        self.animation.setEndValue(QPoint(self.x(), y))  # End at the desired position
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)  # Make the transition smoother
        self.animation.start()

        self.show()
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def on_tray_icon_activated(self, reason):
        if reason in [QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick]:
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
    try:
        script_path = os.path.abspath(sys.argv[0])
        exe_path = script_path.replace('.py', '.exe') if script_path.endswith('.py') else script_path
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "BrightnessController", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Could not set autostart: {e}")


def main():
    app = QApplication(sys.argv)
    enable_autostart()
    window = BrightnessApp()

    # Do not automatically show the window after app starts
    # window.show_window()  # Comment out or remove this line for the auto-show issue.

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
