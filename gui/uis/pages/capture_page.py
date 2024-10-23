import json
import os
import sys

from PySide6.QtCore import QCoreApplication, QPoint
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, Qt, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QPushButton, QGridLayout, QVBoxLayout, QLabel, QHBoxLayout, QWidget, \
    QMainWindow, QSizePolicy, QDialog
from gui.core.json_settings import Settings
from gui.core.functions import Functions
from gui.core.json_themes import Themes
from gui.widgets import PyGroupbox, PyPushButton, PyLoggerWindow
from rotation import RotationThread
from .key_binding import KeyBindDialog

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPainter, QPen, QMouseEvent
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton, QMainWindow


class CaptureWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.point1 = None
        self.point2 = None
        self.capturing = False

    def start_capture(self):
        """Start capturing mouse clicks."""
        self.capturing = True
        self.point1 = None
        self.point2 = None
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        """Capture mouse clicks for defining the rectangular area."""
        if self.capturing and event.button() == Qt.LeftButton:
            if not self.point1:
                self.point1 = event.position().toPoint()
                print(f"Top-left corner selected at: {self.point1}")
            elif not self.point2:
                self.point2 = event.position().toPoint()
                print(f"Bottom-right corner selected at: {self.point2}")
                self.capturing = False
                self.update()  # Trigger a repaint to draw the rectangle

    def paintEvent(self, event):
        """Draw the selection rectangle when both points are selected."""
        if self.point1 and self.point2:
            painter = QPainter(self)
            pen = QPen(Qt.red, 2, Qt.SolidLine)
            painter.setPen(pen)

            # Calculate the rectangle coordinates
            top_left = QPoint(min(self.point1.x(), self.point2.x()), min(self.point1.y(), self.point2.y()))
            rect_width = abs(self.point2.x() - self.point1.x())
            rect_height = abs(self.point2.y() - self.point1.y())

            # Draw the rectangle
            painter.drawRect(top_left.x(), top_left.y(), rect_width, rect_height)

current_dir = os.path.dirname(os.path.abspath(__file__))
gui_dir = os.path.join(current_dir, "..", "..")

class Ui_CapturePage(QMainWindow):  # 继承自 QMainWindow
    def __init__(self, main_window: QMainWindow):
        super().__init__()  # 调用父类构造函数
        self.main_window = main_window
        self.settings = Settings()

        self.point1 = None
        self.point2 = None

        # 是否开始捕获
        self.capturing = False

    def setupUi(self, capture_layout):
        themes = Themes()
        self.themes = themes.items

        # buttons
        self.button_layout = QHBoxLayout(capture_layout)
        self.start_button = PyPushButton(
            text="Capture",
            radius=8,
            color=self.themes["app_color"]["white"],
            bg_color=self.themes["app_color"]["bg_three"],
            bg_color_hover=self.themes["app_color"]["context_hover"],
            bg_color_pressed=self.themes["app_color"]["context_pressed"],
            font_size=15
        )

        self.start_button.clicked.connect(self.start_capture)
        self.button_layout.addWidget(self.start_button)

        self.label_info = QLabel(capture_layout)
        self.button_layout.addWidget(self.label_info)

        # 设置捕获页面的主窗口
        self.setCentralWidget(capture_layout)

    def start_capture(self):
        """开始捕获鼠标点击的左上角和右下角"""
        self.capturing = True
        self.point1 = None
        self.point2 = None
        self.label_info.setText("Click to select top-left corner")

    def mousePressEvent(self, event: QMouseEvent):
        print("C")
        """处理鼠标点击事件"""
        if self.capturing and event.button() == Qt.LeftButton:
            if not self.point1:
                # 获取左上角点
                self.point1 = event.globalPos()
                self.label_info.setText("Click to select bottom-right corner")
                print(f"Top-left corner selected at: {self.point1}")
            elif not self.point2:
                # 获取右下角点
                self.point2 = event.globalPos()
                print(f"Bottom-right corner selected at: {self.point2}")
                self.capturing = False
                self.label_info.setText("Capture complete")
                self.update()  # 重绘来显示矩形框

    def paintEvent(self, event):
        """重写paintEvent以绘制矩形框"""
        if self.point1 and self.point2:
            painter = QPainter(self)
            pen = QPen(Qt.red, 2, Qt.SolidLine)
            painter.setPen(pen)

            # 计算矩形框的左上角坐标和宽高
            top_left = QPoint(min(self.point1.x(), self.point2.x()), min(self.point1.y(), self.point2.y()))
            bottom_right = QPoint(max(self.point1.x(), self.point2.x()), max(self.point1.y(), self.point2.y()))
            rect_width = abs(self.point2.x() - self.point1.x())
            rect_height = abs(self.point2.y() - self.point1.y())

            # 绘制矩形
            painter.drawRect(top_left.x(), top_left.y(), rect_width, rect_height)


