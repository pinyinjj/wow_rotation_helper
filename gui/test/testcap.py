import sys
import os
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QPen, QPixmap, QGuiApplication, QColor, QClipboard, QRegion
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
        current_pixmap = self.pixmap()
        print(f"height {current_pixmap.height()}, width {current_pixmap.width()}")
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
            self.selection_rect = QRect(QPoint(self.x0, self.y0), QPoint(self.x1, self.y1)).normalized()
            self.update()


    def mouseReleaseEvent(self, event):
        """ Finish the selection process when the left mouse button is released. """
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.x1, self.y1 = event.position().toPoint().x(), event.position().toPoint().y()
            scale_factor = QApplication.primaryScreen().devicePixelRatio()
            self.selection_rect = QRect(QPoint(self.x0, self.y0), QPoint(self.x1, self.y1)).normalized()
            self.update()
            print(scale_factor)
            adjusted_x1 = self.x1 * scale_factor
            adjusted_y1 = self.y1 * scale_factor
            print(f"Top-left corner: ({self.selection_rect.x()}, {self.selection_rect.y()})")
            print(f"Adjusted coordinates: ({adjusted_x1}, {adjusted_y1})")

            # Print the coordinates of the top-left corner of the selection
            print(f"Top-left corner: ({self.selection_rect.x()}, {self.selection_rect.y()})")

            # Save the screenshot to the current directory
            self.save_to_file()

            # Close the full-screen capture window after saving the screenshot
            self.close()

    def save_to_file(self):
        """ Capture the selected area and save it to a file. """
        if not self.selection_rect.isNull():
            # Convert QRect to int to avoid issues with floating point
            x, y, width, height = (self.selection_rect.x(), self.selection_rect.y(),
                                   self.selection_rect.width(), self.selection_rect.height())

            # Crop the screenshot to the selected rectangle
            cropped_screenshot = self.screenshot.copy(x, y, width, height)

            # Define the file name
            file_name = "selected_screenshot.png"
            file_path = os.path.join(os.getcwd(), file_name)

            # Save the cropped screenshot to the file
            cropped_screenshot.save(file_path, "png")
            print(f"Screenshot saved to: {file_path}")

    def paintEvent(self, event):
        """ Draw the selection rectangle and mask the rest of the screen. """
        super().paintEvent(event)
        painter = QPainter(self)

        # Create a region that covers the entire window
        full_region = QRegion(self.rect())

        # Subtract the selection rectangle from the full region to create the mask
        if not self.selection_rect.isNull():
            selection_region = QRegion(self.selection_rect)
            masked_region = full_region.subtracted(selection_region)
        else:
            masked_region = full_region

        # Draw the darkened background (mask) only on the masked region
        painter.setClipRegion(masked_region)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))  # Slightly transparent black (alpha=150)

        # Draw the selection rectangle outline
        if not self.selection_rect.isNull():
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
