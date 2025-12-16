# ///////////////////////////////////////////////////////////////
#
# Icon Selector Dialog
# A dialog for selecting one icon from multiple options
#
# ///////////////////////////////////////////////////////////////

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
    QPushButton, QFrame, QMessageBox, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QIcon
import requests
from io import BytesIO


class IconSelectorDialog(QDialog):
    """Dialog for selecting one icon from multiple options"""
    
    def __init__(self, parent=None, themes=None, icon_options=None):
        super().__init__(parent)
        # Load themes if not provided
        if themes is None:
            from gui.core.json_themes import Themes
            themes_obj = Themes()
            self.themes = themes_obj.items
        else:
            self.themes = themes
        
        self.selected_icon = None  # Store selected icon info
        self.icon_options = icon_options or []  # List of icon info: [{'type': 'spell', 'id': id, 'icon_url': url, 'item_name': name}, ...]
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        # Determine if theme is bright or dark
        bg_one = self.themes['app_color']['bg_one']
        self.is_bright_theme = self._is_bright_color(bg_one)
        
        # Dialog properties
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(600, 500)
        
        # Main container with shadow effect
        self.main_container = QFrame(self)
        self.main_container.setObjectName("main_container")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.main_container)
        
        # Container layout
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(24, 24, 24, 24)
        container_layout.setSpacing(20)
        
        # Title section
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(12)
        
        title_label = QLabel("选择图标")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_color = self.themes['app_color']['text_title']
        title_label.setStyleSheet(f"color: {title_color};")
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Close button
        close_text_color = self.themes['app_color']['text_title'] if self.is_bright_theme else self.themes['app_color']['text_foreground']
        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {close_text_color};
                border: none;
                border-radius: 16px;
                font-size: 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.themes['app_color']['bg_three']};
            }}
            QPushButton:pressed {{
                background-color: {self.themes['app_color']['bg_two']};
            }}
        """)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        
        container_layout.addLayout(title_layout)
        
        # Divider
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {self.themes['app_color']['bg_three']};")
        container_layout.addWidget(divider)
        
        # Info label
        info_label = QLabel("检测到多个图标，请选择一个：")
        info_label.setStyleSheet(f"color: {self.themes['app_color']['text_foreground']}; font-size: 14pt;")
        container_layout.addWidget(info_label)
        
        # Icons grid
        self.icons_grid = QGridLayout()
        self.icons_grid.setSpacing(15)
        self.icon_widgets = []  # Store icon widgets for selection
        
        # Load and display icons
        self.load_icons()
        
        icons_container = QWidget()
        icons_container.setLayout(self.icons_grid)
        container_layout.addWidget(icons_container)
        
        container_layout.addStretch()
        
        # Button section
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        self.cancel_btn = self.create_modern_button("取消", "secondary")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.confirm_btn = self.create_modern_button("确认", "primary")
        self.confirm_btn.setEnabled(False)  # Disabled until an icon is selected
        self.confirm_btn.clicked.connect(self.accept_selection)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.confirm_btn)
        
        container_layout.addLayout(button_layout)
        
        # Apply stylesheet
        self.apply_stylesheet()
    
    def load_icons(self):
        """Load and display icons"""
        for i, icon_info in enumerate(self.icon_options):
            icon_widget = self.create_icon_widget(icon_info, i)
            self.icon_widgets.append(icon_widget)
            # Arrange in grid: 2 columns
            row = i // 2
            col = i % 2
            self.icons_grid.addWidget(icon_widget, row, col)
    
    def create_icon_widget(self, icon_info, index):
        """Create an icon widget with clickable selection"""
        widget = QFrame()
        widget.setObjectName(f"icon_widget_{index}")
        widget.setFixedSize(250, 150)
        widget.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Icon image
        icon_label = QLabel()
        icon_label.setFixedSize(64, 64)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setScaledContents(True)
        
        # Load icon from URL
        try:
            response = requests.get(icon_info['icon_url'], timeout=10)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                # Scale to fit
                scaled_pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"[ERROR] Failed to load icon: {e}")
            icon_label.setText("图标")
        
        layout.addWidget(icon_label, alignment=Qt.AlignCenter)
        
        # Item name
        name_label = QLabel(icon_info.get('item_name', 'Unknown'))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet(f"color: {self.themes['app_color']['text_foreground']}; font-size: 12pt;")
        layout.addWidget(name_label)
        
        # Type label
        type_label = QLabel(f"类型: {icon_info.get('type', 'unknown').upper()}")
        type_label.setAlignment(Qt.AlignCenter)
        type_label.setStyleSheet(f"color: {self.themes['app_color']['text_description']}; font-size: 10pt;")
        layout.addWidget(type_label)
        
        # Set initial style
        widget.setStyleSheet(f"""
            QFrame#icon_widget_{index} {{
                background-color: {self.themes['app_color']['bg_two']};
                border: 2px solid {self.themes['app_color']['bg_three']};
                border-radius: 8px;
            }}
            QFrame#icon_widget_{index}:hover {{
                background-color: {self.themes['app_color']['bg_three']};
                border-color: {self.themes['app_color']['context_color']};
            }}
        """)
        
        # Store icon info in widget
        widget.icon_info = icon_info
        widget.is_selected = False
        
        # Connect click event
        widget.mousePressEvent = lambda event, w=widget: self.select_icon(w)
        
        return widget
    
    def select_icon(self, widget):
        """Handle icon selection"""
        # Deselect all
        for w in self.icon_widgets:
            w.is_selected = False
            w.setStyleSheet(f"""
                QFrame#icon_widget_{self.icon_widgets.index(w)} {{
                    background-color: {self.themes['app_color']['bg_two']};
                    border: 2px solid {self.themes['app_color']['bg_three']};
                    border-radius: 8px;
                }}
                QFrame#icon_widget_{self.icon_widgets.index(w)}:hover {{
                    background-color: {self.themes['app_color']['bg_three']};
                    border-color: {self.themes['app_color']['context_color']};
                }}
            """)
        
        # Select clicked widget
        widget.is_selected = True
        index = self.icon_widgets.index(widget)
        widget.setStyleSheet(f"""
            QFrame#icon_widget_{index} {{
                background-color: {self.themes['app_color']['context_color']};
                border: 3px solid {self.themes['app_color']['context_color']};
                border-radius: 8px;
            }}
        """)
        
        # Store selected icon
        self.selected_icon = widget.icon_info
        
        # Enable confirm button
        self.confirm_btn.setEnabled(True)
    
    def accept_selection(self):
        """Accept the selected icon"""
        if self.selected_icon:
            self.accept()
        else:
            QMessageBox.warning(self, "未选择", "请先选择一个图标")
    
    def create_modern_button(self, text, style="primary"):
        """Create a modern styled button"""
        btn = QPushButton(text)
        btn.setFixedHeight(42)
        btn.setMinimumWidth(100)
        
        if style == "primary":
            if self.is_bright_theme:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.themes['app_color']['white']};
                        color: {self.themes['app_color']['context_color']};
                        border: 2px solid {self.themes['app_color']['context_color']};
                        border-radius: 8px;
                        padding: 10px 24px;
                        font-size: 14pt;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {self.themes['app_color']['context_color']};
                        color: {self.themes['app_color']['white']};
                    }}
                    QPushButton:pressed {{
                        background-color: {self.themes['app_color']['context_pressed']};
                        color: {self.themes['app_color']['white']};
                    }}
                    QPushButton:disabled {{
                        background-color: {self.themes['app_color']['bg_three']};
                        color: {self.themes['app_color']['text_description']};
                        border-color: {self.themes['app_color']['bg_three']};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.themes['app_color']['context_color']};
                        color: {self.themes['app_color']['white']};
                        border: none;
                        border-radius: 8px;
                        padding: 10px 24px;
                        font-size: 14pt;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {self.themes['app_color']['context_hover']};
                    }}
                    QPushButton:pressed {{
                        background-color: {self.themes['app_color']['context_pressed']};
                    }}
                    QPushButton:disabled {{
                        background-color: {self.themes['app_color']['bg_three']};
                        color: {self.themes['app_color']['text_description']};
                    }}
                """)
        else:
            if self.is_bright_theme:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.themes['app_color']['white']};
                        color: {self.themes['app_color']['text_title']};
                        border: 2px solid {self.themes['app_color']['bg_three']};
                        border-radius: 8px;
                        padding: 10px 24px;
                        font-size: 14pt;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {self.themes['app_color']['bg_three']};
                        border-color: {self.themes['app_color']['context_color']};
                    }}
                    QPushButton:pressed {{
                        background-color: {self.themes['app_color']['bg_two']};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.themes['app_color']['bg_two']};
                        color: {self.themes['app_color']['text_foreground']};
                        border: 2px solid {self.themes['app_color']['bg_three']};
                        border-radius: 8px;
                        padding: 10px 24px;
                        font-size: 14pt;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {self.themes['app_color']['bg_three']};
                        border-color: {self.themes['app_color']['context_color']};
                    }}
                    QPushButton:pressed {{
                        background-color: {self.themes['app_color']['bg_one']};
                    }}
                """)
        
        return btn
    
    def apply_stylesheet(self):
        """Apply stylesheet to the dialog"""
        self.main_container.setStyleSheet(f"""
            #main_container {{
                background-color: {self.themes['app_color']['bg_one']};
                border-radius: 12px;
                border: 1px solid {self.themes['app_color']['bg_two']};
            }}
        """)
        
        # Add shadow effect
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(Qt.black)
        self.main_container.setGraphicsEffect(shadow)
    
    def _is_bright_color(self, hex_color):
        """Check if a hex color is bright (light theme)"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return luminance > 0.5

