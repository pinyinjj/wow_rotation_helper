from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QWidget, QApplication
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

    def add_input_fields(self, fields):
        """Dynamically add input fields (passed as a list of labels)"""
        for field_label in fields:
            self.add_input_field(field_label)

    def add_input_field(self, label_text):
        """Helper function to create a labeled input field"""
        # Create label
        label = QLabel(label_text)

        # Create input field (QLineEdit)
        input_field = QLineEdit()
        input_field.setPlaceholderText(f"Enter {label_text.split()[0]} ID")

        # Create a horizontal layout for the label and input
        input_layout = QHBoxLayout()
        input_layout.addWidget(label)
        input_layout.addWidget(input_field)

        # Create a widget to hold the layout
        input_widget = QWidget()
        input_widget.setLayout(input_layout)

        # Add input widget to main layout
        self.layout().addWidget(input_widget)

    def add_buttons(self):
        """Add OK and Cancel buttons"""
        button_layout = QHBoxLayout()  # Create a layout for buttons

        # OK Button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.on_ok_clicked)  # Connect to custom method
        button_layout.addWidget(ok_button)

        # Cancel Button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.on_cancel_clicked)  # Connect to custom method
        button_layout.addWidget(cancel_button)

        # Add button layout to the main layout of the dialog
        self.layout().addLayout(button_layout)

        # Apply button styles (Optional)
        button_styles = f"""
        QPushButton {{
            background-color: {self.theme.get('button_bg_color', '#4CAF50')};
            color: {self.theme.get('button_text_color', '#fff')};
            font: {self.theme.get('button_text_font', '9pt "Segoe UI"')};
            border-radius: {self.theme.get('button_border_radius', 5)}px;
            border: 2px solid {self.theme.get('button_border_color', '#388E3C')};
            padding: 10px;
        }}
        QPushButton:hover {{
            background-color: {self.theme.get('button_hover_bg_color', '#45A049')};
        }}
        QPushButton:pressed {{
            background-color: {self.theme.get('button_pressed_bg_color', '#388E3C')};
        }}
        """
        self.setStyleSheet(self.styleSheet() + button_styles)

    # Custom method for OK button click
    def on_ok_clicked(self):
        # You can retrieve values from input fields here if needed
        print("OK Button clicked!")
        self.accept()  # Close the dialog and return accept status

    # Custom method for Cancel button click
    def on_cancel_clicked(self):
        print("Cancel Button clicked!")  # Debugging log
        self.reject()  # Close the dialog and return reject status


if __name__ == "__main__":
    # Create the PyDialog instance
    app = QApplication([])

    dialog = PyDialog()

    # Dynamically add input fields (e.g., for Item ID, Trinket ID, and Consumable ID)
    dialog.add_input_fields([
        "Item ID",
        "Trinket ID",
        "Consumable ID"
    ])

    # Optionally, add buttons after input fields
    dialog.add_buttons()

    # Show the dialog
    dialog.exec()  # Start the dialog loop
