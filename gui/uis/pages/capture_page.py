import os
import sys
from PySide6.QtCore import QPoint, Qt  # Import Qt here to access Qt enums like LeftButton and StrongFocus
from PySide6.QtGui import QPainter, QPen, QMouseEvent
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QMainWindow


current_dir = os.path.dirname(os.path.abspath(__file__))
gui_dir = os.path.join(current_dir, "..", "..")

class CaptureWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.point1 = None
        self.point2 = None
        self.capturing = False

        # Ensure the widget can accept mouse events
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

    def start_capture(self):
        """Start capturing mouse clicks."""
        self.capturing = True
        self.point1 = None
        self.point2 = None
        self.update()

        self.setFocus()


    def mousePressEvent(self, event: QMouseEvent):
        """Capture mouse clicks for defining the rectangular area."""
        print("mouse")
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

            # Calculate the top-left and bottom-right points
            top_left = QPoint(min(self.point1.x(), self.point2.x()), min(self.point1.y(), self.point2.y()))
            rect_width = abs(self.point2.x() - self.point1.x())
            rect_height = abs(self.point2.y() - self.point1.y())

            # Draw the rectangle
            painter.drawRect(top_left.x(), top_left.y(), rect_width, rect_height)

class Ui_CapturePage(QMainWindow):
    def __init__(self, main_window: QMainWindow):
        super().__init__()
        self.main_window = main_window
        self.capture_widget = CaptureWidget()  # Use CaptureWidget directly
        self.setCentralWidget(self.capture_widget)

    def setupUi(self, page_capture):
        self.button_layout = QHBoxLayout(page_capture)
        self.start_button = QPushButton("Start Capture")
        self.start_button.clicked.connect(self.capture_widget.start_capture)
        self.button_layout.addWidget(self.start_button)
        self.label_info = QLabel("Press 'Start Capture' to begin")
        layout = QVBoxLayout(page_capture)
        layout.addWidget(self.label_info)




