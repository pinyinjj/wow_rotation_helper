import sys
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QPen, QPixmap, QGuiApplication, QColor, QClipboard
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QMainWindow, QPushButton


class SLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowState(Qt.WindowFullScreen)
        self.setCursor(Qt.CrossCursor)

        self.x0 = self.y0 = self.x1 = self.y1 = 0
        self.is_selecting = False
        self.selection_rect = QRect()
        self.screenshot = None  # Store the full screenshot

    def start_capture(self, screenshot):
        """ Set the full-screen screenshot as the background. """
        self.screenshot = screenshot
        self.setPixmap(QPixmap.fromImage(screenshot))
        self.show()

    def mousePressEvent(self, event):
        """ Start the selection process when the left mouse button is pressed. """
        if event.button() == Qt.LeftButton:
            # Start the selection process
            self.is_selecting = True
            self.x0, self.y0 = event.position().toPoint().x(), event.position().toPoint().y()

    def mouseMoveEvent(self, event):
        """ Update the selection rectangle as the mouse moves. """
        if self.is_selecting:
            self.x1, self.y1 = event.position().toPoint().x(), event.position().toPoint().y()
            self.selection_rect = QRect(QPoint(self.x0, self.y0), QPoint(self.x1, self.y1))
            self.update()

    def mouseReleaseEvent(self, event):
        """ Finish the selection process when the left mouse button is released. """
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.x1, self.y1 = event.position().toPoint().x(), event.position().toPoint().y()
            self.selection_rect = QRect(QPoint(self.x0, self.y0), QPoint(self.x1, self.y1))
            self.update()

            # Copy the selected region to the clipboard
            self.save_to_clipboard()

            # Close the full-screen capture window after saving the screenshot
            self.close()

    def save_to_clipboard(self):
        """ Capture the selected area and save it to the clipboard. """
        if not self.selection_rect.isNull():
            # Crop the screenshot to the selected rectangle
            cropped_screenshot = self.screenshot.copy(self.selection_rect)

            # Copy the cropped screenshot to the clipboard
            clipboard = QGuiApplication.clipboard()
            clipboard.setPixmap(QPixmap.fromImage(cropped_screenshot))
            print("Screenshot copied to clipboard")

    def paintEvent(self, event):
        """ Draw the selection rectangle and mask the rest of the screen. """
        super().paintEvent(event)
        painter = QPainter(self)

        # Draw the darkened background (mask)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))  # Slightly transparent black (alpha=150)

        if not self.selection_rect.isNull():
            # Clear the selected area to show it with normal brightness
            painter.fillRect(self.selection_rect, QColor(0, 0, 0, 0))  # Fully transparent to clear selection

            # Draw the selection rectangle outline
            pen = QPen(Qt.red, 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(self.selection_rect)


class ScreenShotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ScreenShot Tool")
        self.setGeometry(100, 100, 300, 200)

        # Button to start capturing screenshot
        self.button = QPushButton("Capture Screen", self)
        self.button.clicked.connect(self.start_capture)
        layout = QVBoxLayout()
        layout.addWidget(self.button)

        container = QLabel(self)
        container.setLayout(layout)
        self.setCentralWidget(container)

    def start_capture(self):
        """ Capture the current screen and show the full-screen screenshot interface. """
        screen = QGuiApplication.primaryScreen()
        screenshot = screen.grabWindow(0).toImage()

        self.capture_window = SLabel()
        self.capture_window.start_capture(screenshot)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScreenShotWindow()
    window.show()
    sys.exit(app.exec())
