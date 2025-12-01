# ///////////////////////////////////////////////////////////////
#
# Modern Add Icon Dialog
# A beautiful, modern dialog for adding icons with multiple ID support
#
# ///////////////////////////////////////////////////////////////

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
    QLineEdit, QPushButton, QFrame, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
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
        # Animation for downloading dots
        self.download_dots_timer = QTimer()
        self.download_dots_index = 0
        self.download_dots_pattern = [".", "..", "...", "..", "."]  # . .. ... .. . cycle
        self.download_base_text = ""  # Store base text without dots
        self.download_dots_timer.timeout.connect(self.update_download_dots)
        self.setup_ui()
        print("[DEBUG] ModernAddIconDialog setup complete")
        
    def setup_ui(self):
        """Setup the modern UI"""
        # Determine if theme is bright or dark for consistent color choices
        bg_one = self.themes['app_color']['bg_one']
        self.is_bright_theme = self._is_bright_color(bg_one)
        
        # Dialog properties
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.base_height = 460  # Base height without progress
        self.progress_height = 520  # Height with progress bar
        self.setFixedSize(520, self.base_height)  # Start with base height
        
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
        
        # Title icon and text - use text_title which should have good contrast
        title_icon = QLabel("✨")
        title_icon.setStyleSheet("font-size: 24px;")
        title_icon.setFixedSize(32, 32)
        
        title_label = QLabel("Add Icons")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title_label.setFont(title_font)
        # text_title should work for both themes, but ensure it's dark enough for bright themes
        title_color = self.themes['app_color']['text_title']
        title_label.setStyleSheet(f"color: {title_color};")
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Close button - use text_title for better visibility in bright themes
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
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # Left align for better readability of ID list
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
        print("[DEBUG] Connecting download button click signal")
        # Test if button click works
        def test_click():
            print("[DEBUG] Download button clicked!")
            self.start_download()
        self.download_btn.clicked.connect(test_click)
        print("[DEBUG] Download button connected")
        
        # Set download button as default button so Enter key triggers it
        self.download_btn.setDefault(True)
        self.download_btn.setAutoDefault(True)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.download_btn)
        
        container_layout.addLayout(button_layout)
        
        # Apply stylesheet
        self.apply_stylesheet()
        
        # Ensure button is visible and enabled (will be visible when dialog is shown)
        self.download_btn.setVisible(True)
        self.download_btn.setEnabled(True)
        
        # Connect Enter key from all input fields to download button
        if hasattr(self, 'spell_input'):
            self.spell_input.returnPressed.connect(lambda: self.download_btn.click() if self.download_btn.isEnabled() else None)
        if hasattr(self, 'trinket_input'):
            self.trinket_input.returnPressed.connect(lambda: self.download_btn.click() if self.download_btn.isEnabled() else None)
        if hasattr(self, 'consumable_input'):
            self.consumable_input.returnPressed.connect(lambda: self.download_btn.click() if self.download_btn.isEnabled() else None)
        
    def create_input_group(self, label_text, placeholder, field_name):
        """Create a modern input group"""
        group = QFrame()
        group.setObjectName(f"{field_name}_group")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Label - use appropriate text color based on theme
        label_text_color = self.themes['app_color']['text_title'] if self.is_bright_theme else self.themes['app_color']['text_foreground']
        
        label = QLabel(label_text)
        label_font = QFont()
        label_font.setPointSize(14)
        label_font.setBold(True)
        label.setFont(label_font)
        label.setStyleSheet(f"color: {label_text_color};")
        layout.addWidget(label)
        
        # Input field - use white/light background for better visibility in bright themes
        # Choose appropriate input background colors based on theme
        if self.is_bright_theme:
            input_bg = self.themes['app_color']['white']
            input_bg_focus = self.themes['app_color']['bg_three']
            input_text_color = self.themes['app_color']['text_title']  # Darker text for better contrast
        else:
            input_bg = self.themes['app_color']['dark_one']
            input_bg_focus = self.themes['app_color']['dark_two']
            input_text_color = self.themes['app_color']['text_foreground']
        
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setObjectName(f"{field_name}_input")
        input_field.setFixedHeight(44)  # Increased height for larger font
        input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {input_bg};
                color: {input_text_color};
                border: 2px solid {self.themes['app_color']['bg_two']};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14pt;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.themes['app_color']['context_color']};
                background-color: {input_bg_focus};
            }}
            QLineEdit::placeholder {{
                color: {self.themes['app_color']['text_description']};
            }}
        """)
        layout.addWidget(input_field)
        
        # Store reference
        setattr(self, f"{field_name}_input", input_field)
        
        # Connect Enter key to download button (will be connected after download_btn is created)
        # This will be done in setup_ui after all inputs are created
        
        return group
    
    def create_modern_button(self, text, style="primary"):
        """Create a modern styled button with white theme support"""
        btn = QPushButton(text)
        btn.setFixedHeight(42)
        btn.setMinimumWidth(100)
        
        if style == "primary":
            # Primary button - use context color for bright theme, or white background with context color text
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
            # Secondary button - white style for bright theme
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
        print("[DEBUG] start_download called")
        # Parse inputs
        spell_ids = self.parse_ids(self.spell_input.text().strip())
        trinket_ids = self.parse_ids(self.trinket_input.text().strip())
        consumable_ids = self.parse_ids(self.consumable_input.text().strip())
        
        print(f"[DEBUG] Parsed IDs - Spells: {spell_ids}, Trinkets: {trinket_ids}, Consumables: {consumable_ids}")
        
        # Validate
        if not spell_ids and not trinket_ids and not consumable_ids:
            print("[DEBUG] No IDs entered, showing error")
            self.show_status("Please enter at least one ID", "error")
            return
        
        # Disable buttons and show status
        self.download_btn.setEnabled(False)
        self.cancel_btn.setText("Cancel")
        total_count = len(spell_ids) + len(trinket_ids) + len(consumable_ids)
        self.download_base_text = f"Downloading {total_count} icon(s)"
        self.download_dots_index = 0
        self.show_status(f"{self.download_base_text}{self.download_dots_pattern[0]}", "info")
        # Start dots animation timer (update every 500ms)
        self.download_dots_timer.start(500)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, total_count)
        self.progress_bar.setValue(0)
        # Increase window height to accommodate progress bar
        self.setFixedSize(520, self.progress_height)
        
        # Import here to avoid circular imports
        from PySide6.QtCore import QThread, Signal
        
        # Create download thread
        class DownloadThread(QThread):
            finished = Signal(bool, str, int, int, list, list)  # success, message, success_count, fail_count, failed_ids, failed_ids_detail
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
                print(f"[DEBUG] DownloadThread.run() started")
                print(f"[DEBUG] Class: {self.class_name}, Talent: {self.talent_name}, Version: {self.game_version}")
                success_count = 0
                fail_count = 0
                failed_ids = []  # Track failed IDs for display
                failed_ids_detail = []  # Track failed IDs with detail info: {'type': 'spell', 'id': id}
                total = len(self.spell_ids) + len(self.trinket_ids) + len(self.consumable_ids)
                print(f"[DEBUG] Total items to download: {total}")
                
                # Download spells
                for spell_id in self.spell_ids:
                    print(f"[DEBUG] Downloading spell: {spell_id}")
                    if self._is_cancelled:
                        break
                    try:
                        print(f"[DEBUG] Calling Functions.download_icon for spell {spell_id}")
                        # Convert ID to int if it's a string
                        spell_id_int = int(spell_id) if isinstance(spell_id, str) and spell_id.isdigit() else spell_id
                        status = Functions.download_icon(
                            spell_id=spell_id_int,
                            class_name=self.class_name,
                            talent_name=self.talent_name,
                            game_version=self.game_version
                        )
                        print(f"[DEBUG] download_icon returned status: {status}")
                        self._current_progress += 1
                        self.progress.emit(self._current_progress)
                        if status == 1:
                            success_count += 1
                        else:
                            fail_count += 1
                            failed_ids.append(f"Spell ID: {spell_id}")
                            failed_ids_detail.append({'type': 'spell', 'id': spell_id_int})
                            print(f"[ERROR] 下载失败 - Spell ID: {spell_id}")
                    except Exception as e:
                        fail_count += 1
                        failed_ids.append(f"Spell ID: {spell_id}")
                        spell_id_int = int(spell_id) if isinstance(spell_id, str) and spell_id.isdigit() else spell_id
                        failed_ids_detail.append({'type': 'spell', 'id': spell_id_int})
                        print(f"[ERROR] 下载失败 - Spell ID: {spell_id}, 错误: {e}")
                        self._current_progress += 1
                        self.progress.emit(self._current_progress)
                
                # Download trinkets
                for trinket_id in self.trinket_ids:
                    print(f"[DEBUG] Downloading trinket: {trinket_id}")
                    if self._is_cancelled:
                        break
                    try:
                        print(f"[DEBUG] Calling Functions.download_icon for trinket {trinket_id}")
                        # Convert ID to int if it's a string
                        trinket_id_int = int(trinket_id) if isinstance(trinket_id, str) and trinket_id.isdigit() else trinket_id
                        status = Functions.download_icon(
                            trinket_id=trinket_id_int,
                            class_name=self.class_name,
                            talent_name=self.talent_name,
                            game_version=self.game_version
                        )
                        print(f"[DEBUG] download_icon returned status: {status}")
                        self._current_progress += 1
                        self.progress.emit(self._current_progress)
                        if status == 1:
                            success_count += 1
                        else:
                            fail_count += 1
                            failed_ids.append(f"Trinket ID: {trinket_id}")
                            failed_ids_detail.append({'type': 'trinket', 'id': trinket_id_int})
                            print(f"[ERROR] 下载失败 - Trinket ID: {trinket_id}")
                    except Exception as e:
                        fail_count += 1
                        failed_ids.append(f"Trinket ID: {trinket_id}")
                        trinket_id_int = int(trinket_id) if isinstance(trinket_id, str) and trinket_id.isdigit() else trinket_id
                        failed_ids_detail.append({'type': 'trinket', 'id': trinket_id_int})
                        print(f"[ERROR] 下载失败 - Trinket ID: {trinket_id}, 错误: {e}")
                        self._current_progress += 1
                        self.progress.emit(self._current_progress)
                
                # Download consumables
                for consumable_id in self.consumable_ids:
                    print(f"[DEBUG] Downloading consumable: {consumable_id}")
                    if self._is_cancelled:
                        break
                    try:
                        print(f"[DEBUG] Calling Functions.download_icon for consumable {consumable_id}")
                        # Convert ID to int if it's a string
                        consumable_id_int = int(consumable_id) if isinstance(consumable_id, str) and consumable_id.isdigit() else consumable_id
                        status = Functions.download_icon(
                            consumable_id=consumable_id_int,
                            class_name=self.class_name,
                            talent_name=self.talent_name,
                            game_version=self.game_version
                        )
                        print(f"[DEBUG] download_icon returned status: {status}")
                        self._current_progress += 1
                        self.progress.emit(self._current_progress)
                        if status == 1:
                            success_count += 1
                        else:
                            fail_count += 1
                            failed_ids.append(f"Consumable ID: {consumable_id}")
                            failed_ids_detail.append({'type': 'consumable', 'id': consumable_id_int})
                            print(f"[ERROR] 下载失败 - Consumable ID: {consumable_id}")
                    except Exception as e:
                        fail_count += 1
                        failed_ids.append(f"Consumable ID: {consumable_id}")
                        consumable_id_int = int(consumable_id) if isinstance(consumable_id, str) and consumable_id.isdigit() else consumable_id
                        failed_ids_detail.append({'type': 'consumable', 'id': consumable_id_int})
                        print(f"[ERROR] 下载失败 - Consumable ID: {consumable_id}, 错误: {e}")
                        self._current_progress += 1
                        self.progress.emit(self._current_progress)
                
                # Emit result with failed IDs
                if success_count > 0:
                    if failed_ids:
                        message = f"Successfully downloaded {success_count} icon(s), {fail_count} failed"
                    else:
                        message = f"Successfully downloaded {success_count} icon(s)"
                    self.finished.emit(True, message, success_count, fail_count, failed_ids, failed_ids_detail)
                else:
                    message = f"Failed to download {fail_count} icon(s)"
                    self.finished.emit(False, message, success_count, fail_count, failed_ids, failed_ids_detail)
            
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
            print(f"[DEBUG] Got from page_instance - Class: {class_name}, Talent: {talent_name}, Version: {game_version}")
        else:
            # Fallback if page_instance not set
            class_name = ''
            talent_name = ''
            game_version = 'retail'
            print("[DEBUG] page_instance not found, using defaults")
        
        print(f"[DEBUG] Creating DownloadThread with - Class: {class_name}, Talent: {talent_name}, Version: {game_version}")
        self.download_thread = DownloadThread(
            spell_ids, trinket_ids, consumable_ids,
            class_name, talent_name, game_version
        )
        
        def on_progress(value):
            self.progress_bar.setValue(value)
        
        def on_finished(success, message, success_count, fail_count, failed_ids, failed_ids_detail):
            # Stop dots animation
            self.download_dots_timer.stop()
            self.progress_bar.setVisible(False)
            
            # 如果有失败的ID，弹窗显示并提供重新下载选项
            if failed_ids:
                failed_list = "\n".join([f"  • {failed_id}" for failed_id in failed_ids])
                error_message = f"以下图标下载失败，未找到对应的图标：\n\n{failed_list}"
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("图标下载失败")
                msg_box.setText(error_message)
                
                # 添加重新下载按钮
                retry_btn = msg_box.addButton("重新下载", QMessageBox.ActionRole)
                ok_btn = msg_box.addButton("确定", QMessageBox.AcceptRole)
                
                result = msg_box.exec()
                
                # 如果用户点击了重新下载按钮
                if msg_box.clickedButton() == retry_btn:
                    # 重新下载失败的图标
                    self.retry_download_failed_icons(failed_ids_detail)
                    return
            
            if success:
                # Build message with failed IDs if any
                if failed_ids:
                    failed_list = "\n".join([f"  • {failed_id}" for failed_id in failed_ids])
                    full_message = f"{message}\n\nFailed Icon IDs:\n{failed_list}"
                    self.show_status(full_message, "success")
                    # Adjust window height for failed IDs list
                    estimated_lines = 3 + len(failed_ids)  # Base message + failed IDs
                    additional_height = max(0, (estimated_lines - 3) * 20)
                    new_height = min(self.progress_height + additional_height, 600)  # Max 600px
                    self.setFixedSize(520, new_height)
                else:
                    self.show_status(message, "success")
                # Auto close after 1.5 seconds (or longer if there are failures)
                from PySide6.QtCore import QTimer
                delay = 3000 if failed_ids else 1500  # Longer delay if there are failures
                def close_and_reload():
                    self.accept()
                    if hasattr(self, 'reload_icons') and callable(self.reload_icons):
                        self.reload_icons()
                QTimer.singleShot(delay, close_and_reload)
            else:
                # Build message with failed IDs
                if failed_ids:
                    failed_list = "\n".join([f"  • {failed_id}" for failed_id in failed_ids])
                    full_message = f"{message}\n\nFailed Icon IDs:\n{failed_list}"
                    self.show_status(full_message, "error")
                    # Adjust window height for failed IDs list
                    estimated_lines = 3 + len(failed_ids)  # Base message + failed IDs
                    additional_height = max(0, (estimated_lines - 3) * 20)
                    new_height = min(self.progress_height + additional_height, 600)  # Max 600px
                    self.setFixedSize(520, new_height)
                else:
                    self.show_status(message, "error")
                self.download_btn.setEnabled(True)
                self.cancel_btn.setText("Close")
                # Keep window at progress height if showing error, user can close manually
        
        self.download_thread.progress.connect(on_progress)
        self.download_thread.finished.connect(on_finished)
        print("[DEBUG] Starting download thread")
        self.download_thread.start()
    
    def update_download_dots(self):
        """Update the downloading dots animation"""
        if self.download_base_text:
            self.download_dots_index = (self.download_dots_index + 1) % len(self.download_dots_pattern)
            dots = self.download_dots_pattern[self.download_dots_index]
            self.status_label.setText(f"{self.download_base_text}{dots}")
    
    def show_status(self, message, status_type="info"):
        """Show status message with different styles"""
        # Stop dots animation if showing a different status
        if status_type != "info" or not message.startswith("Downloading"):
            self.download_dots_timer.stop()
            self.download_base_text = ""
        self.status_frame.setVisible(True)
        self.status_label.setText(message)
        # Adjust status frame height based on message length and line count
        line_count = message.count('\n') + 1
        if line_count > 3:
            # For messages with failed ID list, calculate height based on lines
            base_height = 50
            additional_height = (line_count - 1) * 20  # ~20px per additional line
            self.status_frame.setFixedHeight(min(base_height + additional_height, 200))  # Max 200px
        elif len(message) > 50:
            self.status_frame.setFixedHeight(70)  # More height for longer messages
        else:
            self.status_frame.setFixedHeight(50)  # Standard height
        
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
    
    def _is_bright_color(self, hex_color):
        """Check if a hex color is bright (light theme)"""
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        # Calculate luminance (perceived brightness)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        # If luminance > 0.5, it's a bright color
        return luminance > 0.5
    
    def retry_download_failed_icons(self, failed_ids_detail):
        """重新下载失败的图标"""
        if not failed_ids_detail:
            return
        
        # 分离不同类型的ID
        spell_ids = []
        trinket_ids = []
        consumable_ids = []
        
        for item in failed_ids_detail:
            if item['type'] == 'spell':
                spell_ids.append(str(item['id']))
            elif item['type'] == 'trinket':
                trinket_ids.append(str(item['id']))
            elif item['type'] == 'consumable':
                consumable_ids.append(str(item['id']))
        
        # 设置输入框的值（用于下载）
        self.spell_input.setText(",".join(spell_ids))
        self.trinket_input.setText(",".join(trinket_ids))
        self.consumable_input.setText(",".join(consumable_ids))
        
        # 重新开始下载
        self.start_download()
    
    def reload_icons(self):
        """Reload icons - to be set by parent"""
        pass
    
    def closeEvent(self, event):
        """Handle close event"""
        self.download_dots_timer.stop()
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.cancel()
            self.download_thread.wait()
        event.accept()
    
    def reject(self):
        """Handle cancel/close"""
        self.download_dots_timer.stop()
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.cancel()
            self.download_thread.wait()
        super().reject()

