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
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont
from gui.core.functions import Functions
from gui.widgets.py_icon_selector_dialog import IconSelectorDialog


class DownloadThread(QThread):
    """下载图标的线程类"""
    finished = Signal(bool, str, int, int, list, list, dict)
    progress = Signal(int)
    
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
        self.multiple_icons_info = None
    
    def cancel(self):
        """取消下载"""
        self._is_cancelled = True
    
    def _convert_id_to_int(self, item_id):
        """将ID转换为整数（如果是字符串）"""
        if isinstance(item_id, str) and item_id.isdigit():
            return int(item_id)
        return item_id
    
    def _download_single_item(self, item_id, item_type, class_name, talent_name, game_version):
        """下载单个物品图标"""
        try:
            item_id_int = self._convert_id_to_int(item_id)
            kwargs = {
                'class_name': class_name,
                'talent_name': talent_name,
                'game_version': game_version
            }
            kwargs[f'{item_type}_id'] = item_id_int
            
            status = Functions.download_icon(**kwargs)
            self._current_progress += 1
            self.progress.emit(self._current_progress)
            return status, item_id_int
        except Exception as e:
            self._current_progress += 1
            self.progress.emit(self._current_progress)
            print(f"[ERROR] 下载失败 - {item_type} ID: {item_id}, 错误: {e}")
            item_id_int = self._convert_id_to_int(item_id)
            return -1, item_id_int
    
    def _get_first_id(self, id_list):
        """获取ID列表的第一个ID并转换为整数（如果可能）"""
        if not id_list:
            return None
        first_id = id_list[0]
        if isinstance(first_id, str) and first_id.isdigit():
            return int(first_id)
        return first_id
    
    def _create_failed_ids_detail(self, spell_id, trinket_id, consumable_id):
        """创建失败ID详情列表"""
        failed_ids_detail = []
        if spell_id is not None:
            failed_ids_detail.append({'type': 'spell', 'id': spell_id})
        if trinket_id is not None:
            failed_ids_detail.append({'type': 'trinket', 'id': trinket_id})
        if consumable_id is not None:
            failed_ids_detail.append({'type': 'consumable', 'id': consumable_id})
        return failed_ids_detail
    
    def _handle_classic_multiple_types(self):
        """处理classic模式下多个类型的ID"""
        spell_id = self._get_first_id(self.spell_ids)
        trinket_id = self._get_first_id(self.trinket_ids)
        consumable_id = self._get_first_id(self.consumable_ids)
        
        try:
            result = Functions.download_icon(
                spell_id=spell_id,
                trinket_id=trinket_id,
                consumable_id=consumable_id,
                class_name=self.class_name,
                talent_name=self.talent_name,
                game_version=self.game_version
            )
            self._current_progress += 1
            self.progress.emit(self._current_progress)
            
            return self._process_download_result(result, spell_id, trinket_id, consumable_id)
        except Exception as e:
            self._current_progress += 1
            self.progress.emit(self._current_progress)
            print(f"[ERROR] 下载失败，错误: {e}")
            failed_ids_detail = self._create_failed_ids_detail(spell_id, trinket_id, consumable_id)
            return -1, failed_ids_detail
    
    def _process_download_result(self, result, spell_id, trinket_id, consumable_id):
        """处理下载结果"""
        if isinstance(result, dict) and result.get('multiple_icons'):
            self.multiple_icons_info = result.get('icons', [])
            return 0, []  # 需要用户选择
        
        if result == 1:
            return 1, []
        
        # 下载失败
        failed_ids_detail = self._create_failed_ids_detail(spell_id, trinket_id, consumable_id)
        return -1, failed_ids_detail
    
    def _download_items_list(self, item_ids, item_type):
        """下载物品列表"""
        success_count = 0
        failed_ids = []
        failed_ids_detail = []
        
        for item_id in item_ids:
            if self._is_cancelled:
                break
            status, item_id_int = self._download_single_item(
                item_id, item_type, self.class_name, self.talent_name, self.game_version
            )
            if status == 1:
                success_count += 1
            else:
                failed_ids.append(f"{item_type.capitalize()} ID: {item_id}")
                failed_ids_detail.append({'type': item_type, 'id': item_id_int})
        
        return success_count, failed_ids, failed_ids_detail
    
    def run(self):
        """运行下载线程"""
        print(f"[DEBUG] DownloadThread.run() started")
        print(f"[DEBUG] Class: {self.class_name}, Talent: {self.talent_name}, Version: {self.game_version}")
        
        success_count = 0
        fail_count = 0
        failed_ids = []
        failed_ids_detail = []
        total = len(self.spell_ids) + len(self.trinket_ids) + len(self.consumable_ids)
        print(f"[DEBUG] Total items to download: {total}")
        
        is_classic = self.game_version.lower() == "classic"
        has_multiple_types = sum([
            len(self.spell_ids) > 0,
            len(self.trinket_ids) > 0,
            len(self.consumable_ids) > 0
        ]) > 1
        
        if is_classic and has_multiple_types:
            status, detail = self._handle_classic_multiple_types()
            if status == 1:
                success_count += 1
            elif status == -1:
                fail_count += 1
                failed_ids_detail.extend(detail)
                for item in detail:
                    failed_ids.append(f"{item['type'].capitalize()} ID: {item['id']}")
        else:
            # 下载spells
            if self.spell_ids:
                sc, fi, fid = self._download_items_list(self.spell_ids, 'spell')
                success_count += sc
                failed_ids.extend(fi)
                failed_ids_detail.extend(fid)
            
            # 下载trinkets
            if self.trinket_ids:
                sc, fi, fid = self._download_items_list(self.trinket_ids, 'trinket')
                success_count += sc
                failed_ids.extend(fi)
                failed_ids_detail.extend(fid)
            
            # 下载consumables
            if self.consumable_ids:
                sc, fi, fid = self._download_items_list(self.consumable_ids, 'consumable')
                success_count += sc
                failed_ids.extend(fi)
                failed_ids_detail.extend(fid)
            
            fail_count = len(failed_ids)
        
        # 发送结果
        multiple_icons_dict = {'icons': self.multiple_icons_info} if self.multiple_icons_info else {}
        
        if success_count > 0:
            message = f"Successfully downloaded {success_count} icon(s)" + (f", {fail_count} failed" if failed_ids else "")
        else:
            message = f"Failed to download {fail_count} icon(s)"
        
        self.finished.emit(
            success_count > 0, message, success_count, fail_count,
            failed_ids, failed_ids_detail, multiple_icons_dict
        )


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
    
    def _get_page_info(self):
        """从page_instance获取类名、天赋名和游戏版本"""
        if not hasattr(self, 'page_instance'):
            return '', '', 'retail'
        
        page = self.page_instance
        class_name = getattr(page, 'selected_class_name', '')
        talent_name = getattr(page, 'selected_talent_name', '')
        
        if hasattr(page, 'get_game_version'):
            game_version = page.get_game_version()
        elif 'classic' in str(type(page).__name__).lower():
            game_version = 'classic'
        else:
            game_version = 'retail'
        
        return class_name, talent_name, game_version
    
    def _prepare_download_ui(self, total_count):
        """准备下载UI（禁用按钮、显示进度等）"""
        self.download_btn.setEnabled(False)
        self.cancel_btn.setText("Cancel")
        self.download_base_text = f"Downloading {total_count} icon(s)"
        self.download_dots_index = 0
        self.show_status(f"{self.download_base_text}{self.download_dots_pattern[0]}", "info")
        self.download_dots_timer.start(500)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, total_count)
        self.progress_bar.setValue(0)
        self.setFixedSize(520, self.progress_height)
    
    def _handle_multiple_icons_selection(self, icon_options):
        """处理多个图标选择"""
        selector_dialog = IconSelectorDialog(
            parent=self,
            themes=self.themes,
            icon_options=icon_options
        )
        
        parent_rect = self.geometry()
        dialog_rect = selector_dialog.geometry()
        x = parent_rect.x() + (parent_rect.width() - dialog_rect.width()) // 2
        y = parent_rect.y() + (parent_rect.height() - dialog_rect.height()) // 2
        selector_dialog.move(x, y)
        
        if selector_dialog.exec() == QDialog.Accepted:
            selected_icon = selector_dialog.selected_icon
            if selected_icon:
                self._download_selected_icon(selected_icon)
            else:
                self._handle_selection_cancelled()
        else:
            self._handle_selection_cancelled()
    
    def _download_selected_icon(self, selected_icon):
        """下载选中的图标"""
        try:
            download_status = Functions.download_and_save_icon(
                icon_url=selected_icon['icon_url'],
                item_name=selected_icon['item_name'],
                item_id=selected_icon['id'],
                class_name=self._saved_class_name,
                talent_name=self._saved_talent_name,
                game_version=self._saved_game_version
            )
            
            if download_status == 1:
                self.show_status(f"成功下载图标: {selected_icon.get('item_name', 'Unknown')}", "success")
                from PySide6.QtCore import QTimer
                def close_and_reload():
                    self.accept()
                    if hasattr(self, 'reload_icons') and callable(self.reload_icons):
                        self.reload_icons()
                QTimer.singleShot(1500, close_and_reload)
            else:
                self.show_status(f"下载图标失败: {selected_icon.get('item_name', 'Unknown')}", "error")
                self.download_btn.setEnabled(True)
                self.cancel_btn.setText("Close")
        except Exception as e:
            print(f"[ERROR] Failed to download selected icon: {e}")
            self.show_status(f"下载图标时发生错误: {str(e)}", "error")
            self.download_btn.setEnabled(True)
            self.cancel_btn.setText("Close")
    
    def _handle_selection_cancelled(self):
        """处理用户取消选择"""
        self.show_status("用户取消了图标选择", "info")
        self.download_btn.setEnabled(True)
        self.cancel_btn.setText("Close")
    
    def _handle_failed_downloads(self, failed_ids, failed_ids_detail):
        """处理下载失败的情况"""
        is_multiple_icons_error = any("多个链接找到图标" in failed_id for failed_id in failed_ids)
        
        if is_multiple_icons_error:
            error_message = "错误：多个链接找到图标\n\n请只输入一个类型的ID（Spell ID、Trinket ID 或 Consumable ID 中的一种）"
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("多个链接找到图标")
            msg_box.setText(error_message)
            msg_box.addButton("确定", QMessageBox.AcceptRole)
            msg_box.exec()
            self.download_btn.setEnabled(True)
            self.cancel_btn.setText("Close")
            return False
        
        failed_list = "\n".join([f"  • {failed_id}" for failed_id in failed_ids])
        error_message = f"以下图标下载失败，未找到对应的图标：\n\n{failed_list}"
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("图标下载失败")
        msg_box.setText(error_message)
        
        retry_btn = msg_box.addButton("重新下载", QMessageBox.ActionRole)
        msg_box.addButton("确定", QMessageBox.AcceptRole)
        msg_box.exec()
        
        if msg_box.clickedButton() == retry_btn:
            self.retry_download_failed_icons(failed_ids_detail)
            return False
        
        return True
    
    def _adjust_window_for_failed_ids(self, failed_ids):
        """根据失败的ID数量调整窗口高度"""
        if not failed_ids:
            return
        estimated_lines = 3 + len(failed_ids)
        additional_height = max(0, (estimated_lines - 3) * 20)
        new_height = min(self.progress_height + additional_height, 600)
        self.setFixedSize(520, new_height)
    
    def _handle_successful_download(self, message, failed_ids):
        """处理成功下载的情况"""
        if failed_ids:
            failed_list = "\n".join([f"  • {failed_id}" for failed_id in failed_ids])
            full_message = f"{message}\n\nFailed Icon IDs:\n{failed_list}"
            self.show_status(full_message, "success")
            self._adjust_window_for_failed_ids(failed_ids)
        else:
            self.show_status(message, "success")
        
        from PySide6.QtCore import QTimer
        delay = 3000 if failed_ids else 1500
        def close_and_reload():
            self.accept()
            if hasattr(self, 'reload_icons') and callable(self.reload_icons):
                self.reload_icons()
        QTimer.singleShot(delay, close_and_reload)
    
    def _handle_failed_download(self, message, failed_ids):
        """处理完全失败的情况"""
        if failed_ids:
            failed_list = "\n".join([f"  • {failed_id}" for failed_id in failed_ids])
            full_message = f"{message}\n\nFailed Icon IDs:\n{failed_list}"
            self.show_status(full_message, "error")
            self._adjust_window_for_failed_ids(failed_ids)
        else:
            self.show_status(message, "error")
        self.download_btn.setEnabled(True)
        self.cancel_btn.setText("Close")
    
    def _on_download_finished(self, success, message, success_count, fail_count, failed_ids, failed_ids_detail, multiple_icons_info):
        """处理下载完成的回调"""
        self.download_dots_timer.stop()
        self.progress_bar.setVisible(False)
        
        # 处理多个图标选择
        if multiple_icons_info and multiple_icons_info.get('icons'):
            icon_options = multiple_icons_info.get('icons', [])
            print(f"[DEBUG] Showing icon selector dialog with {len(icon_options)} options")
            self._handle_multiple_icons_selection(icon_options)
            return
        
        # 处理失败的下载
        if failed_ids:
            if not self._handle_failed_downloads(failed_ids, failed_ids_detail):
                return
        
        # 处理成功或失败的结果
        if success:
            self._handle_successful_download(message, failed_ids)
        else:
            self._handle_failed_download(message, failed_ids)
    
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
        
        # Prepare UI
        total_count = len(spell_ids) + len(trinket_ids) + len(consumable_ids)
        self._prepare_download_ui(total_count)
        
        # Get page info
        class_name, talent_name, game_version = self._get_page_info()
        print(f"[DEBUG] Creating DownloadThread with - Class: {class_name}, Talent: {talent_name}, Version: {game_version}")
        
        # Save for callbacks
        self._saved_class_name = class_name
        self._saved_talent_name = talent_name
        self._saved_game_version = game_version
        
        # Create and start thread
        self.download_thread = DownloadThread(
            spell_ids, trinket_ids, consumable_ids,
            class_name, talent_name, game_version
        )
        
        self.download_thread.progress.connect(lambda value: self.progress_bar.setValue(value))
        self.download_thread.finished.connect(self._on_download_finished)
        
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

