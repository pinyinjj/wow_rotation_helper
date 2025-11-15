# ///////////////////////////////////////////////////////////////
#
# Modern Add Icon Dialog
# A beautiful, modern dialog for adding icons with multiple ID support
#
# ///////////////////////////////////////////////////////////////

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
    QLineEdit, QPushButton, QFrame, QProgressBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from gui.core.functions import Functions


class ModernAddIconDialog(QDialog):
    """Modern dialog for adding icons with multiple ID support"""
    
    def __init__(self, parent=None, themes=None):
        super().__init__(parent)
        # Load themes if not provided
        if themes is None:
            from gui.core.json_themes import Themes
            themes_obj = Themes()
            self.themes = themes_obj.items
        else:
            self.themes = themes
        self.download_thread = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the modern UI"""
        # Dialog properties
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(520, 460)  # Increased size to accommodate larger fonts
        
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
        
        # Title icon and text
        title_icon = QLabel("✨")
        title_icon.setStyleSheet("font-size: 24px;")
        title_icon.setFixedSize(32, 32)
        
        title_label = QLabel("Add Icons")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {self.themes['app_color']['text_title']};")
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.themes['app_color']['text_foreground']};
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
        
        # Input fields section
        input_layout = QVBoxLayout()
        input_layout.setSpacing(16)
        
        # Spell ID input
        spell_group = self.create_input_group(
            "Spell ID",
            "Enter spell IDs (comma, space, or semicolon separated)",
            "spell"
        )
        input_layout.addWidget(spell_group)
        
        # Trinket ID input
        trinket_group = self.create_input_group(
            "Trinket ID",
            "Enter trinket IDs (comma, space, or semicolon separated)",
            "trinket"
        )
        input_layout.addWidget(trinket_group)
        
        # Consumable ID input
        consumable_group = self.create_input_group(
            "Consumable ID",
            "Enter consumable IDs (comma, space, or semicolon separated)",
            "consumable"
        )
        input_layout.addWidget(consumable_group)
        
        container_layout.addLayout(input_layout)
        
        # Status section
        self.status_frame = QFrame()
        self.status_frame.setFixedHeight(50)
        self.status_frame.setVisible(False)
        status_layout = QVBoxLayout(self.status_frame)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)
        
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {self.themes['app_color']['bg_two']};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {self.themes['app_color']['context_color']};
                border-radius: 3px;
            }}
        """)
        status_layout.addWidget(self.progress_bar)
        
        container_layout.addWidget(self.status_frame)
        
        # Button section
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        self.cancel_btn = self.create_modern_button("Cancel", "secondary")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.download_btn = self.create_modern_button("Download", "primary")
        self.download_btn.clicked.connect(self.start_download)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.download_btn)
        
        container_layout.addLayout(button_layout)
        
        # Apply stylesheet
        self.apply_stylesheet()
        
    def create_input_group(self, label_text, placeholder, field_name):
        """Create a modern input group"""
        group = QFrame()
        group.setObjectName(f"{field_name}_group")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Label
        label = QLabel(label_text)
        label_font = QFont()
        label_font.setPointSize(14)
        label_font.setBold(True)
        label.setFont(label_font)
        label.setStyleSheet(f"color: {self.themes['app_color']['text_foreground']};")
        layout.addWidget(label)
        
        # Input field
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setObjectName(f"{field_name}_input")
        input_field.setFixedHeight(44)  # Increased height for larger font
        input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.themes['app_color']['dark_one']};
                color: {self.themes['app_color']['text_foreground']};
                border: 2px solid {self.themes['app_color']['bg_two']};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14pt;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.themes['app_color']['context_color']};
                background-color: {self.themes['app_color']['dark_two']};
            }}
            QLineEdit::placeholder {{
                color: {self.themes['app_color']['text_description']};
            }}
        """)
        layout.addWidget(input_field)
        
        # Store reference
        setattr(self, f"{field_name}_input", input_field)
        
        return group
    
    def create_modern_button(self, text, style="primary"):
        """Create a modern styled button"""
        btn = QPushButton(text)
        btn.setFixedHeight(42)
        btn.setMinimumWidth(100)
        
        if style == "primary":
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
        """Apply modern stylesheet to the dialog"""
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
    
    def parse_ids(self, id_string):
        """Parse ID string supporting multiple separators"""
        if not id_string or not id_string.strip():
            return []
        # Replace all separators with comma
        id_string = id_string.replace('，', ',')  # Chinese comma
        id_string = id_string.replace(';', ',')   # Semicolon
        id_string = id_string.replace(' ', ',')    # Space
        # Split and clean
        ids = [id.strip() for id in id_string.split(',') if id.strip()]
        return ids
    
    def start_download(self):
        """Start the download process"""
        # Parse inputs
        spell_ids = self.parse_ids(self.spell_input.text().strip())
        trinket_ids = self.parse_ids(self.trinket_input.text().strip())
        consumable_ids = self.parse_ids(self.consumable_input.text().strip())
        
        # Validate
        if not spell_ids and not trinket_ids and not consumable_ids:
            self.show_status("Please enter at least one ID", "error")
            return
        
        # Disable buttons and show status
        self.download_btn.setEnabled(False)
        self.cancel_btn.setText("Cancel")
        total_count = len(spell_ids) + len(trinket_ids) + len(consumable_ids)
        self.show_status(f"Downloading {total_count} icon(s)...", "info")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, total_count)
        self.progress_bar.setValue(0)
        
        # Import here to avoid circular imports
        from PySide6.QtCore import QThread, Signal
        
        # Create download thread
        class DownloadThread(QThread):
            finished = Signal(bool, str, int, int)  # success, message, success_count, fail_count
            progress = Signal(int)  # current progress
            
            def __init__(self, spell_ids, trinket_ids, consumable_ids, class_name, talent_name, game_version):
                super().__init__()
                self.spell_ids = spell_ids
                self.trinket_ids = trinket_ids
                self.consumable_ids = consumable_ids
                self.class_name = class_name
                self.talent_name = talent_name
                self.game_version = game_version
                self._is_cancelled = False
                self._current_progress = 0
            
            def run(self):
                success_count = 0
                fail_count = 0
                total = len(self.spell_ids) + len(self.trinket_ids) + len(self.consumable_ids)
                
                # Download spells
                for spell_id in self.spell_ids:
                    if self._is_cancelled:
                        break
                    try:
                        status = Functions.download_icon(
                            spell_id=spell_id,
                            class_name=self.class_name,
                            talent_name=self.talent_name,
                            game_version=self.game_version
                        )
                        self._current_progress += 1
                        self.progress.emit(self._current_progress)
                        if status == 1:
                            success_count += 1
                        else:
                            fail_count += 1
                    except Exception as e:
                        print(f"Error downloading spell {spell_id}: {e}")
                        self._current_progress += 1
                        self.progress.emit(self._current_progress)
                        fail_count += 1
                
                # Download trinkets
                for trinket_id in self.trinket_ids:
                    if self._is_cancelled:
                        break
                    try:
                        status = Functions.download_icon(
                            trinket_id=trinket_id,
                            class_name=self.class_name,
                            talent_name=self.talent_name,
                            game_version=self.game_version
                        )
                        self._current_progress += 1
                        self.progress.emit(self._current_progress)
                        if status == 1:
                            success_count += 1
                        else:
                            fail_count += 1
                    except Exception as e:
                        print(f"Error downloading trinket {trinket_id}: {e}")
                        self._current_progress += 1
                        self.progress.emit(self._current_progress)
                        fail_count += 1
                
                # Download consumables
                for consumable_id in self.consumable_ids:
                    if self._is_cancelled:
                        break
                    try:
                        status = Functions.download_icon(
                            consumable_id=consumable_id,
                            class_name=self.class_name,
                            talent_name=self.talent_name,
                            game_version=self.game_version
                        )
                        self._current_progress += 1
                        self.progress.emit(self._current_progress)
                        if status == 1:
                            success_count += 1
                        else:
                            fail_count += 1
                    except Exception as e:
                        print(f"Error downloading consumable {consumable_id}: {e}")
                        self._current_progress += 1
                        self.progress.emit(self._current_progress)
                        fail_count += 1
                
                # Emit result
                if success_count > 0:
                    self.finished.emit(True, f"Successfully downloaded {success_count} icon(s)", success_count, fail_count)
                else:
                    self.finished.emit(False, f"Failed to download {fail_count} icon(s)", success_count, fail_count)
            
            def cancel(self):
                self._is_cancelled = True
        
        # Get class and talent names from page_instance (set by the page)
        if hasattr(self, 'page_instance'):
            page = self.page_instance
            class_name = getattr(page, 'selected_class_name', '')
            talent_name = getattr(page, 'selected_talent_name', '')
            # Determine game version based on page class name
            if 'classic' in str(type(page).__name__).lower():
                game_version = 'classic'
            else:
                game_version = 'retail'
        else:
            # Fallback if page_instance not set
            class_name = ''
            talent_name = ''
            game_version = 'retail'
        
        self.download_thread = DownloadThread(
            spell_ids, trinket_ids, consumable_ids,
            class_name, talent_name, game_version
        )
        
        def on_progress(value):
            self.progress_bar.setValue(value)
        
        def on_finished(success, message, success_count, fail_count):
            self.progress_bar.setVisible(False)
            if success:
                self.show_status(message, "success")
                # Auto close after 1.5 seconds
                from PySide6.QtCore import QTimer
                def close_and_reload():
                    self.accept()
                    if hasattr(self, 'reload_icons') and callable(self.reload_icons):
                        self.reload_icons()
                QTimer.singleShot(1500, close_and_reload)
            else:
                self.show_status(message, "error")
                self.download_btn.setEnabled(True)
                self.cancel_btn.setText("Close")
        
        self.download_thread.progress.connect(on_progress)
        self.download_thread.finished.connect(on_finished)
        self.download_thread.start()
    
    def show_status(self, message, status_type="info"):
        """Show status message with different styles"""
        self.status_frame.setVisible(True)
        self.status_label.setText(message)
        
        color_map = {
            "info": self.themes['app_color']['context_color'],
            "success": self.themes['app_color']['green'],
            "error": self.themes['app_color']['red']
        }
        
        self.status_label.setStyleSheet(f"""
            color: {color_map.get(status_type, color_map['info'])};
            font-size: 13pt;
            font-weight: 500;
        """)
    
    def reload_icons(self):
        """Reload icons - to be set by parent"""
        pass
    
    def closeEvent(self, event):
        """Handle close event"""
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.cancel()
            self.download_thread.wait()
        event.accept()
    
    def reject(self):
        """Handle cancel/close"""
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.cancel()
            self.download_thread.wait()
        super().reject()

