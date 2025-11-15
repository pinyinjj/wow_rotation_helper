from PySide6.QtWidgets import QDialog, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt

# Import Themes (assuming Themes() returns a dictionary with theme properties)
from gui.core.json_themes import Themes


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

        print("Initializing PyDialog...")  # Debug

        # Load theme settings
        themes = Themes()
        self.theme = themes.items

        # Dialog properties
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setModal(True)  # Ensures the dialog blocks interaction until closed

        # Create a central widget and layout
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)

        # Apply theme settings to dialog
        self.setStyleSheet(self.create_stylesheet())

        # Set the central widget layout to the dialog layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(central_widget)

        print("PyDialog initialized.")  # Debug

    def create_stylesheet(self):
        """Generate stylesheet using theme settings"""
        bg_color = self.theme.get('bg_color', '#2c313c')
        text_color = self.theme.get('text_color', '#fff')
        text_font = self.theme.get('text_font', "16pt 'Segoe UI'")
        border_radius = self.theme.get('border_radius', 10)
        border_size = self.theme.get('border_size', 2)
        border_color = self.theme.get('border_color', '#343b48')

        stylesheet = f"""
        QDialog {{
            background-color: {bg_color};
            color: {text_color};
            font: {text_font};
            border-radius: {border_radius}px;
            border: {border_size}px solid {border_color};
        }}
        QLabel {{
            color: {text_color}; 
            font: {text_font};    
        }}
        """
        return stylesheet

