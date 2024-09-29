from PySide6.QtWidgets import QGroupBox

class PyGroupbox(QGroupBox):
    def __init__(self, title, themes, parent=None):
        super().__init__(title, parent)
        self.themes = themes
        self.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {self.themes["app_color"]["bg_three"]};
                border-radius: 10px;
                background-color: {self.themes["app_color"]["bg_two"]};
                margin-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: {self.themes["app_color"]["text_title"]};
            }}
        """)


