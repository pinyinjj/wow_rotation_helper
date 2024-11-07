
import json
import os
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

# IMPORT THEMES
# ///////////////////////////////////////////////////////////////
from gui.core.json_themes import Themes  # Import Themes

# PY DIALOG
# ///////////////////////////////////////////////////////////////
class PyDialog(QDialog):
    def __init__(
        self,
        parent=None,
        layout=Qt.Vertical,
        margin=10,
        spacing=5,
        window_title="Custom Dialog"
    ):
        super().__init__(parent)

        # LOAD THEMES
        # ///////////////////////////////////////////////////////////////
        themes = Themes()  # Load the current theme
        self.theme = themes.items  # Get the loaded theme items

        # PROPERTIES
        # ///////////////////////////////////////////////////////////////
        self.setWindowTitle(window_title)

        # Basic dialog setup
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(margin, margin, margin, margin)
        self.layout().setSpacing(spacing)

        # Apply theme settings to the dialog
        self.setStyleSheet(self.create_stylesheet())

        # Add a simple label to test
        test_label = QLabel("Test Content - PyDialog")
        self.layout().addWidget(test_label)

    def create_stylesheet(self):
        """Generate stylesheet using theme settings"""
        bg_color = self.theme.get('bg_color', '#2c313c')  # Default to dark background
        text_color = self.theme.get('text_color', '#fff')  # Default to white text
        text_font = self.theme.get('text_font', "9pt 'Segoe UI'")
        border_radius = self.theme.get('border_radius', 10)
        border_size = self.theme.get('border_size', 2)
        border_color = self.theme.get('border_color', '#343b48')

        # Creating the stylesheet
        stylesheet = f"""
        background-color: {bg_color};
        color: {text_color};
        font: {text_font};
        border-radius: {border_radius}px;
        border: {border_size}px solid {border_color};
        """
        return stylesheet

