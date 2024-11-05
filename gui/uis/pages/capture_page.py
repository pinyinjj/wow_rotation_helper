import sys
import os
from PySide6.QtCore import Qt, QRect, QPoint, QSize
from PySide6.QtGui import QPainter, QPen, QPixmap, QGuiApplication, QColor, QRegion, QIcon
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QMainWindow, QPushButton, QHBoxLayout, QFileDialog

from gui.core.functions import Functions

class Ui_CapturePage(QMainWindow):
    def __init__(self, main_window: QMainWindow):
        super().__init__()
        self.main_window = main_window
        self.is_selecting = False
        self.x0 = self.y0 = self.x1 = self.y1 = 0
        self.selection_rect = QRect()
        self.screenshot = None  # Store the full screenshot


    def setupUi(self, capture_page):
        self.cropped_image_label = QLabel(self)
        self.cropped_image_label.setFixedSize(200, 200)
        self.cropped_image_label.setStyleSheet("border: 1px solid black;")

        self.start_button = self.create_button("trim_icon.svg")
        self.start_button.setText("Capture")
        self.start_button.clicked.connect(self.start_capture)

        self.save_icon_button = self.create_button("save_icon.svg")
        self.save_icon_button.setText("Save Icon")
        self.save_icon_button.clicked.connect(self.save_as)

        self.capture_page_layout = QVBoxLayout(capture_page)
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.start_button)
        self.button_layout.addWidget(self.save_icon_button)
        self.capture_page_layout.addWidget(self.cropped_image_label)
        self.capture_page_layout.addLayout(self.button_layout)

        self.full_screen_label = QLabel()
        self.full_screen_label.setGeometry(QGuiApplication.primaryScreen().geometry())
        self.full_screen_label.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

    def save_as(self):
        """ Save the cropped screenshot to a user-selected directory. """
        if self.cropped_image_label.pixmap() is None:
            print("No image to save.")
            return

        # Open a dialog to select the save file path
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "", "PNG Files (*.png);;All Files (*)"
        )

        if file_path:
            # Save the pixmap from cropped_image_label as an image file
            self.cropped_image_label.pixmap().save(file_path, "PNG")
            print(f"Screenshot saved to: {file_path}")

    def create_button(self, icon="icon_heart.svg", size=40):
        button = QPushButton()
        icon_path = Functions.set_svg_icon(icon)
        button.setIcon(QIcon(icon_path))
        button.setFixedSize(size + 100, size)
        button.setIconSize(QSize(size - 10, size - 10))
        button.setStyleSheet("""
            QPushButton {
                background-color: #343b48;
                border-radius: 8px;
                color: #c3ccdf;
                border: 2px solid #343b48;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #3c4454;
                color: #dce1ec;
                border-color: #3c4454;
            }
            QPushButton:pressed {
                background-color: #2c313c;
                color: #edf0f5;
                border-color: #2c313c;
            }
            QPushButton:checked {
                background-color: #1b1e23;
                color: #f5f6f9;
                border-color: #568af2;
            }
        """)
        return button

    def start_capture(self):
        """ Capture the current screen and start the selection process. """
        # Grab the current screen's screenshot
        screen = QGuiApplication.primaryScreen()
        self.screenshot = screen.grabWindow(0).toImage()

        self.x0 = self.y0 = self.x1 = self.y1 = 0
        self.is_selecting = False
        self.selection_rect = QRect()

        # Display the screenshot in the full-screen label
        self.full_screen_label.setPixmap(QPixmap.fromImage(self.screenshot))
        self.full_screen_label.setVisible(True)
        self.full_screen_label.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.full_screen_label.setCursor(Qt.CrossCursor)
        self.showFullScreen()

    def mousePressEvent(self, event):
        """ Start the selection process when the left mouse button is pressed. """
        if event.button() == Qt.LeftButton:
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

            # Adjust coordinates
            adjusted_x0, adjusted_y0 = int(self.x0 * scale_factor), int(self.y0 * scale_factor)
            adjusted_x1, adjusted_y1 = int(self.x1 * scale_factor), int(self.y1 * scale_factor)

            # Extract the selected area
            width = abs(adjusted_x1 - adjusted_x0)
            height = abs(adjusted_y1 - adjusted_y0)
            cropped_image = self.screenshot.copy(adjusted_x0, adjusted_y0, width, height)

            # Display the cropped image
            self.display_cropped_image(cropped_image)

            # Restore window settings
            self.setWindowFlags(Qt.Widget)
            self.setWindowState(Qt.WindowNoState)
            self.setCursor(Qt.ArrowCursor)
            # self.show()

    def display_cropped_image(self, cropped_image):
        """ Display the cropped screenshot in the QLabel widget. """
        if cropped_image:
            pixmap = QPixmap.fromImage(cropped_image)
            image_width = pixmap.width()
            image_height = pixmap.height()

            # If the image exceeds 300x300, scale it proportionally
            if image_width > 300 or image_height > 300:
                pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            # Adjust the label size to the image size or keep it 200x200 minimum
            self.cropped_image_label.setFixedSize(
                max(200, pixmap.width()), max(200, pixmap.height())
            )

            self.cropped_image_label.setPixmap(pixmap)

    def paintEvent(self, event):
        """ Draw the selection rectangle and mask the rest of the screen. """
        if self.screenshot:
            painter = QPainter(self)
            painter.drawPixmap(0, 0, QPixmap.fromImage(self.screenshot))

            # Mask the rest of the screen
            full_region = QRegion(self.rect())
            if not self.selection_rect.isNull():
                selection_region = QRegion(self.selection_rect)
                masked_region = full_region.subtracted(selection_region)
            else:
                masked_region = full_region

            painter.setClipRegion(masked_region)
            painter.fillRect(self.rect(), QColor(0, 0, 0, 150))  # Transparent black

            # Draw the selection rectangle
            if not self.selection_rect.isNull():
                pen = QPen(Qt.red, 2, Qt.SolidLine)
                painter.setPen(pen)
                painter.drawRect(self.selection_rect)

