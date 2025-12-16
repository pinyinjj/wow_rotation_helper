# ///////////////////////////////////////////////////////////////
#
# Base Class Page
# Common functionality for both retail and classic class pages
#
# ///////////////////////////////////////////////////////////////

import os
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSizePolicy, QMainWindow, QMenu, QMessageBox, QInputDialog, QDoubleSpinBox, QDialog, QDialogButtonBox, QFrame, QPushButton, QGraphicsDropShadowEffect
from PySide6.QtGui import QIcon, Qt, QFont, QColor
from PySide6.QtCore import QCoreApplication
from gui.core.functions import Functions
from gui.widgets import PyPushButton
from ...widgets.py_add_icon_dialog import ModernAddIconDialog


class BaseClassPage:
    """Base class for both retail and classic class pages"""
    
    def __init__(self, main_window: QMainWindow, game_version: str = 'retail'):
        """
        初始化基类
        
        参数:
            main_window: 主窗口实例
            game_version: 游戏版本，'retail' 或 'classic'
        """
        self.main_window = main_window
        self.game_version = game_version.lower()  # 确保是小写
        self.themes = None  # 将在 setupUi 中初始化
        
        # 用于存储图标widget和路径的字典
        self.icon_widgets = {}  # 存储所有图标widget，key为图标名称，value为icon_widget
        self.icon_paths = {}  # 存储图标路径，key为图标名称，value为图标文件路径
        
    def get_game_version(self):
        """返回游戏版本"""
        return self.game_version
    
    def show_add_icon_dialog(self):
        """Displays a modern dialog for adding icons."""
        # Create modern dialog with main_window as parent
        dialog = ModernAddIconDialog(parent=self.main_window, themes=self.themes)
        
        # Set page instance reference for accessing selected_class_name and selected_talent_name
        dialog.page_instance = self
        
        # Set reload callback
        dialog.reload_icons = self.reload_icons
        
        # Center dialog on main window
        dialog.move(
            self.main_window.x() + (self.main_window.width() - 520) // 2,
            self.main_window.y() + (self.main_window.height() - 460) // 2
        )
        
        # Show dialog
        dialog.exec()
    
    def create_add_icon_button(self):
        """Creates a custom 'Add Icon' button that opens the add icon dialog on click."""
        # 根据背景颜色自动选择文字颜色
        bg_color = self.themes["app_color"]["bg_one"]
        bg_color_hover = self.themes["app_color"]["context_hover"]
        bg_color_pressed = self.themes["app_color"]["context_pressed"]
        
        text_color = self.get_contrast_text_color(bg_color)
        hover_text_color = self.get_contrast_text_color(bg_color_hover)
        pressed_text_color = self.get_contrast_text_color(bg_color_pressed)
        
        # Create button with custom styling
        add_icon_button = PyPushButton(
            text="Add Icon",
            radius=8,
            color=text_color,
            bg_color=bg_color,
            bg_color_hover=bg_color_hover,
            bg_color_pressed=bg_color_pressed,
            font_size=20
        )
        
        # 更新样式以支持不同状态的文字颜色
        updated_style = f"""
QPushButton {{
	border: none;
    padding-left: 10px;
    padding-right: 5px;
    color: {text_color};
	border-radius: 8px;	
	background-color: {bg_color};
	font-size: 20px;
}}
QPushButton:hover {{
	background-color: {bg_color_hover};
	color: {hover_text_color};
}}
QPushButton:pressed {{	
	background-color: {bg_color_pressed};
	color: {pressed_text_color};
}}
"""
        add_icon_button.setStyleSheet(updated_style)

        add_icon_button.setFixedHeight(64)
        add_icon_button.setFixedWidth(80)
        add_icon_button.setToolTip("Add a new icon")

        # Connect button click to open the dialog
        add_icon_button.clicked.connect(self.show_add_icon_dialog)

        return add_icon_button

    def create_add_icon_widget(self, icon='icon_heart.svg', button_text="Add Icon"):
        """
        Creates a widget with an empty icon placeholder and an 'Add Icon' button.
        
        参数:
            icon: 图标文件名
            button_text: 按钮文本，子类可以覆盖以自定义
        """
        # Create an empty icon placeholder
        icon_label = QLabel()
        icon_label.setFixedSize(64, 64)
        icon_label.setScaledContents(True)

        icon_path = Functions.set_svg_icon(icon)
        try:
            icon_label.setPixmap(QIcon(icon_path).pixmap(64, 64))
        except Exception as e:
            print(f"加载图标错误: {e}")
            icon_label.setText("No Icon")

        # Set up the layout for the icon placeholder
        icon_layout = QVBoxLayout()
        icon_layout.addWidget(icon_label)

        icon_widget = QWidget()
        icon_widget.setLayout(icon_layout)
        icon_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Create the 'Add Icon' button
        add_icon_button = self.create_add_icon_button()
        add_icon_button.setText(button_text)

        # Combine the icon and button in a horizontal layout
        add_icon_layout = QHBoxLayout()
        add_icon_layout.setAlignment(Qt.AlignLeft)
        add_icon_layout.setSpacing(5)
        add_icon_layout.addWidget(icon_widget)
        add_icon_layout.addWidget(add_icon_button)

        # Wrap the layout in a widget
        add_icon_ability_widget = QWidget()
        add_icon_ability_widget.setLayout(add_icon_layout)

        return add_icon_ability_widget

    def get_contrast_text_color(self, bg_color):
        """根据背景颜色返回对比度高的文字颜色"""
        # 将十六进制颜色转换为RGB
        bg_color = bg_color.lstrip('#')
        r = int(bg_color[0:2], 16)
        g = int(bg_color[2:4], 16)
        b = int(bg_color[4:6], 16)
        
        # 计算亮度 (使用相对亮度公式)
        brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        
        # 如果背景较亮，返回深色文字；如果背景较暗，返回浅色文字
        if brightness > 0.5:
            return self.themes["app_color"]["text_title"]  # 深色文字
        else:
            return self.themes["app_color"]["white"]  # 浅色文字
    
    def reload_icons(self):
        """
        重新加载图标
        子类需要实现此方法
        """
        raise NotImplementedError("Subclasses must implement reload_icons method")
    
    def create_icon_widget(self, icon_path, tooltip_text):
        """
        创建带右键菜单的图标widget
        
        参数:
            icon_path: 图标文件路径
            tooltip_text: 工具提示文本（也是图标名称）
        
        返回:
            QWidget: 包含图标的widget
        """
        icon_label = QLabel()
        icon_label.setFixedSize(64, 64)
        icon_label.setScaledContents(True)

        try:
            icon_label.setPixmap(QIcon(icon_path).pixmap(64, 64))
        except Exception as e:
            print(f"加载图标错误: {e}")
            icon_label.setText("No Icon")

        icon_label.setToolTip(tooltip_text)
        
        # 启用右键菜单
        icon_label.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # 连接右键菜单信号
        def show_context_menu(pos):
            menu = QMenu(self.main_window)
            
            # 设置菜单样式，与主界面主题一致
            bg_color = self.themes["app_color"]["bg_one"]
            hover_color = self.themes["app_color"]["context_hover"]
            text_color = self.themes["app_color"]["text_foreground"]
            border_color = self.themes["app_color"]["bg_two"]
            
            menu.setStyleSheet(f"""
                QMenu {{
                    background-color: {bg_color};
                    color: {text_color};
                    border: 1px solid {border_color};
                    border-radius: 8px;
                    padding: 4px;
                    font-size: 16px;
                    font-weight: 500;
                }}
                QMenu::item {{
                    background-color: transparent;
                    padding: 12px 24px;
                    border-radius: 4px;
                    min-width: 120px;
                }}
                QMenu::item:selected {{
                    background-color: {hover_color};
                    color: {self.themes["app_color"]["white"]};
                }}
            """)
            
            # Add "Set Threshold" action for talent abilities
            # Check if this is a talent ability (has config_data attribute)
            if hasattr(self, 'config_data') and hasattr(self, 'save_config_with_rules'):
                set_threshold_action = menu.addAction("Set Threshold")
                set_threshold_action.setFont(QFont("Segoe UI", 16, QFont.Bold))
                set_threshold_action.triggered.connect(lambda: self.set_threshold(tooltip_text))
            
            delete_action = menu.addAction("Delete Icon")
            delete_action.setFont(QFont("Segoe UI", 16, QFont.Bold))
            delete_action.triggered.connect(lambda: self.delete_icon(tooltip_text, icon_path))
            menu.exec(icon_label.mapToGlobal(pos))
        
        icon_label.customContextMenuRequested.connect(show_context_menu)

        icon_layout = QVBoxLayout()
        icon_layout.addWidget(icon_label)

        icon_widget = QWidget()
        icon_widget.setLayout(icon_layout)
        icon_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        return icon_widget
    
    def _get_current_threshold(self, ability_name):
        """获取当前阈值（如果存在）"""
        if not hasattr(self, 'config_data') or ability_name not in self.config_data:
            return None
        
        config_value = self.config_data[ability_name]
        if isinstance(config_value, list) and len(config_value) >= 2:
            return config_value[1]
        return None
    
    def _create_threshold_spinbox(self, current_threshold):
        """创建阈值输入框"""
        threshold_spin = QDoubleSpinBox()
        threshold_spin.setRange(0.3, 0.9)
        threshold_spin.setSingleStep(0.1)
        threshold_spin.setDecimals(2)
        threshold_spin.setValue(float(current_threshold) if current_threshold is not None else 0.5)
        return threshold_spin
    
    def _create_threshold_dialog_title(self, container_layout):
        """创建对话框标题部分"""
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(12)
        
        title_label = QLabel("Set Threshold")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {self.themes['app_color']['text_title']};")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 32)
        bg_three = self.themes["app_color"]["bg_three"]
        bg_two = self.themes["app_color"]["bg_two"]
        text_title = self.themes["app_color"]["text_title"]
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {text_title};
                border: none;
                border-radius: 16px;
                font-size: 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {bg_three};
            }}
            QPushButton:pressed {{
                background-color: {bg_two};
            }}
        """)
        title_layout.addWidget(close_btn)
        return title_layout, close_btn
    
    def _create_threshold_dialog_buttons(self, dialog):
        """创建对话框按钮部分"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        bg_two = self.themes["app_color"]["bg_two"]
        bg_three = self.themes["app_color"]["bg_three"]
        text_color = self.themes["app_color"]["text_foreground"]
        context_color = self.themes["app_color"]["context_color"]
        context_hover = self.themes["app_color"]["context_hover"]
        context_pressed = self.themes["app_color"]["context_pressed"]
        
        cancel_btn = QPushButton("Cancel")
        cancel_font = QFont()
        cancel_font.setPointSize(16)
        cancel_font.setBold(True)
        cancel_btn.setFont(cancel_font)
        cancel_btn.setFixedSize(120, 45)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_two};
                color: {text_color};
                border: 2px solid {bg_three};
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {bg_three};
                border: 2px solid {context_hover};
            }}
            QPushButton:pressed {{
                background-color: {bg_two};
            }}
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("Confirm")
        ok_btn.setFont(cancel_font)
        ok_btn.setFixedSize(120, 45)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {context_color};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {context_hover};
            }}
            QPushButton:pressed {{
                background-color: {context_pressed};
            }}
        """)
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        
        return button_layout
    
    def _setup_threshold_dialog_ui(self, dialog, main_container, container_layout, threshold_spin, ability_name):
        """设置带主题的阈值对话框UI"""
        bg_one = self.themes["app_color"]["bg_one"]
        bg_two = self.themes["app_color"]["bg_two"]
        bg_three = self.themes["app_color"]["bg_three"]
        text_color = self.themes["app_color"]["text_foreground"]
        text_title = self.themes["app_color"]["text_title"]
        context_color = self.themes["app_color"]["context_color"]
        context_hover = self.themes["app_color"]["context_hover"]
        
        # 标题部分
        title_layout, close_btn = self._create_threshold_dialog_title(container_layout)
        close_btn.clicked.connect(dialog.reject)
        container_layout.addLayout(title_layout)
        
        # 分隔线
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {bg_three};")
        container_layout.addWidget(divider)
        
        # 说明标签
        label = QLabel(f"Set threshold for '{ability_name}'\n(Range: 0.3 - 0.9)")
        label.setWordWrap(True)
        label_font = QFont()
        label_font.setPointSize(16)
        label.setFont(label_font)
        label.setStyleSheet(f"color: {text_color}; padding: 8px 0px;")
        container_layout.addWidget(label)
        
        # 设置输入框样式
        spin_font = QFont()
        spin_font.setPointSize(18)
        threshold_spin.setFont(spin_font)
        threshold_spin.setFixedHeight(50)
        threshold_spin.setStyleSheet(f"""
            QDoubleSpinBox {{
                background-color: {bg_two};
                color: {text_color};
                border: 2px solid {bg_three};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 18px;
            }}
            QDoubleSpinBox:focus {{
                border: 2px solid {context_color};
            }}
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                background-color: {bg_three};
                border: none;
                width: 30px;
            }}
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
                background-color: {context_hover};
            }}
        """)
        container_layout.addWidget(threshold_spin)
        container_layout.addStretch()
        
        # 按钮部分
        button_layout = self._create_threshold_dialog_buttons(dialog)
        container_layout.addLayout(button_layout)
        
        # 应用样式
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: transparent;
            }}
            QFrame#main_container {{
                background-color: {bg_one};
                border: 1px solid {bg_two};
                border-radius: 12px;
            }}
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 100))
        main_container.setGraphicsEffect(shadow)
    
    def _setup_threshold_dialog_ui_basic(self, dialog, main_container, container_layout, threshold_spin, ability_name):
        """设置基本样式的阈值对话框UI（无主题）"""
        label = QLabel(f"Set threshold for '{ability_name}'\n(Range: 0.3 - 0.9)")
        label.setWordWrap(True)
        container_layout.addWidget(label)
        container_layout.addWidget(threshold_spin)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        container_layout.addWidget(button_box)
        
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2c313c;
            }
            QFrame#main_container {
                background-color: #2c313c;
                border: 1px solid #343b48;
                border-radius: 12px;
            }
        """)
    
    def _update_config_with_threshold(self, ability_name, threshold_value):
        """更新配置数据中的阈值"""
        if not hasattr(self, 'config_data'):
            return
        
        if ability_name in self.config_data:
            config_value = self.config_data[ability_name]
            if isinstance(config_value, list) and len(config_value) >= 2:
                self.config_data[ability_name] = [config_value[0], threshold_value]
            elif isinstance(config_value, str):
                self.config_data[ability_name] = [config_value, threshold_value]
            else:
                self.config_data[ability_name] = [config_value, threshold_value]
        else:
            self.config_data[ability_name] = ["", threshold_value]
    
    def _validate_and_save_threshold(self, ability_name, threshold_value):
        """验证并保存阈值"""
        if threshold_value < 0.3 or threshold_value > 0.9:
            QMessageBox.warning(
                self.main_window,
                "Invalid Threshold",
                "Threshold must be between 0.3 and 0.9"
            )
            return False
        
        confirm_message = f"Confirm threshold modification for '{ability_name}' to {threshold_value:.2f}"
        if not self._show_confirm_dialog("Confirm Threshold Modification", confirm_message):
            return False
        
        self._update_config_with_threshold(ability_name, threshold_value)
        
        if hasattr(self, 'save_config_with_rules'):
            self.save_config_with_rules()
            self._restart_listener_if_running()
            self.show_modern_message(
                "Threshold Set",
                f"Threshold for '{ability_name}' has been set to {threshold_value:.2f}",
                "info"
            )
        return True
    
    def set_threshold(self, ability_name):
        """
        设置技能图标的匹配阈值
        
        参数:
            ability_name: 技能名称
        """
        current_threshold = self._get_current_threshold(ability_name)
        
        # 创建对话框
        dialog = QDialog(self.main_window)
        dialog.setWindowFlag(Qt.FramelessWindowHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setModal(True)
        dialog.setFixedSize(420, 280)
        
        # 主容器
        main_container = QFrame(dialog)
        main_container.setObjectName("main_container")
        
        # 主布局
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_container)
        
        # 容器布局
        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(24, 24, 24, 24)
        container_layout.setSpacing(20)
        
        # 创建阈值输入框
        threshold_spin = self._create_threshold_spinbox(current_threshold)
        
        # 设置UI
        if hasattr(self, 'themes') and self.themes:
            self._setup_threshold_dialog_ui(dialog, main_container, container_layout, threshold_spin, ability_name)
        else:
            self._setup_threshold_dialog_ui_basic(dialog, main_container, container_layout, threshold_spin, ability_name)
        
        # 显示对话框并处理结果
        if dialog.exec() == QDialog.Accepted:
            threshold_value = threshold_spin.value()
            self._validate_and_save_threshold(ability_name, threshold_value)
    
    def _restart_listener_if_running(self):
        """
        如果监听正在运行，重启它以应用新的阈值设置。
        子类可以覆盖此方法以实现特定的重启逻辑。
        """
        # 检查是否有 rotation_thread 属性
        if not hasattr(self, 'rotation_thread'):
            return
        
        # 对于 classic 版本：检查 is_running
        if hasattr(self, 'is_running') and self.is_running:
            if self.rotation_thread and self.rotation_thread.isRunning():
                print("[DEBUG] Restarting listener to apply new threshold settings...", flush=True)
                # 停止当前线程
                self.rotation_thread.stop()
                # 等待线程结束（异步，真正的清理在 on_thread_finished 中）
                # 使用 QTimer 延迟重启，确保线程完全停止
                from PySide6.QtCore import QTimer
                QTimer.singleShot(500, self._restart_classic_listener)
        
        # 对于 retail 版本：检查 rotation_mode
        elif hasattr(self, 'rotation_mode') and self.rotation_mode in ("run", "preview"):
            if self.rotation_thread and self.rotation_thread.isRunning():
                print("[DEBUG] Restarting listener to apply new threshold settings...", flush=True)
                # 保存当前模式
                saved_mode = self.rotation_mode
                # 停止当前线程
                self.rotation_thread.stop()
                # 使用 QTimer 延迟重启，确保线程完全停止
                from PySide6.QtCore import QTimer
                QTimer.singleShot(500, lambda: self._restart_retail_listener(saved_mode))
    
    def _restart_classic_listener(self):
        """重启 classic 版本的监听"""
        if not hasattr(self, 'selected_class_name') or not hasattr(self, 'selected_talent_name'):
            return
        
        # 如果线程还在运行，再等待一下
        if self.rotation_thread and self.rotation_thread.isRunning():
            from PySide6.QtCore import QTimer
            QTimer.singleShot(300, self._restart_classic_listener)
            return
        
        config_filepath = self.load_latest_config()
        if not config_filepath:
            print("Configuration file not found, unable to restart the rotation thread.")
            return
        
        from rotation import RotationThread
        print("Restarting RotationThread after threshold update...")
        self.rotation_thread = RotationThread(
            config_file='rotation_config.yaml',
            keybind_file=config_filepath,
            class_name=self.selected_class_name,
            talent_name=self.selected_talent_name,
            game_version='classic'
        )
        self.rotation_thread.finished.connect(self.on_thread_finished)
        if hasattr(self, 'on_icon_matched'):
            self.rotation_thread.icon_matched.connect(self.on_icon_matched)
        
        self.rotation_thread.start()
        self.is_running = True
        if hasattr(self, 'start_button'):
            from PySide6.QtGui import QIcon
            from gui.core.functions import Functions
            self.start_button.setText("Stop")
            self.start_button.setIcon(QIcon(Functions.set_svg_icon("pause.svg")))
        print("RotationThread restarted.")
    
    def _restart_retail_listener(self, saved_mode):
        """重启 retail 版本的监听"""
        if not hasattr(self, 'selected_class_name') or not hasattr(self, 'selected_talent_name'):
            return
        
        # 如果线程还在运行，再等待一下
        if self.rotation_thread and self.rotation_thread.isRunning():
            from PySide6.QtCore import QTimer
            QTimer.singleShot(300, lambda: self._restart_retail_listener(saved_mode))
            return
        
        config_filepath = self.load_latest_config()
        if not config_filepath:
            print("Configuration file not found, unable to restart the rotation thread.")
            return
        
        from rotation import RotationThread
        print(f"Restarting RotationThread in {saved_mode} mode after threshold update...")
        self.rotation_thread = RotationThread(
            config_file='rotation_config.yaml',
            keybind_file=config_filepath,
            class_name=self.selected_class_name,
            talent_name=self.selected_talent_name,
            game_version='retail'
        )
        self.rotation_thread.finished.connect(self.on_thread_finished)
        if hasattr(self, 'on_icon_matched'):
            self.rotation_thread.icon_matched.connect(self.on_icon_matched)
        
        self.rotation_thread.set_mode(saved_mode)
        self.rotation_thread.start()
        self.rotation_mode = saved_mode
        self.is_running = True
        
        # 更新按钮状态
        if hasattr(self, 'start_button'):
            from PySide6.QtGui import QIcon
            from gui.core.functions import Functions
            if saved_mode == "run":
                self.start_button.setText("Stop")
                self.start_button.setIcon(QIcon(Functions.set_svg_icon("pause.svg")))
            elif saved_mode == "preview":
                self.start_button.setText("Start")
                self.start_button.setIcon(QIcon(Functions.set_svg_icon("start.svg")))
                if hasattr(self, 'preview_button'):
                    self.preview_button.setText("Stop Preview")
                    self.preview_button.setIcon(QIcon(Functions.set_svg_icon("pause.svg")))
                    self.preview_active = True
        print("RotationThread restarted.")
    
    def _calculate_dialog_height(self, message, base_height=280, fixed_part=200):
        """计算对话框高度"""
        message_label_temp = QLabel(message)
        message_label_temp.setWordWrap(True)
        message_label_temp.setFixedWidth(372)
        message_font_temp = QFont()
        message_font_temp.setPointSize(16)
        message_label_temp.setFont(message_font_temp)
        message_label_temp.adjustSize()
        message_height = max(message_label_temp.height(), 40)
        return max(base_height, fixed_part + message_height)
    
    def _create_modern_dialog_base(self, title, message, dialog_width=420):
        """创建现代化对话框的基础结构"""
        dialog = QDialog(self.main_window)
        dialog.setWindowFlag(Qt.FramelessWindowHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setModal(True)
        
        dialog_height = self._calculate_dialog_height(message)
        dialog.setFixedSize(dialog_width, dialog_height)
        
        main_container = QFrame(dialog)
        main_container.setObjectName("main_container")
        
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_container)
        
        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(24, 24, 24, 24)
        container_layout.setSpacing(20)
        
        return dialog, main_container, container_layout
    
    def _create_dialog_title(self, container_layout, title, dialog):
        """创建对话框标题部分"""
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(12)
        
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title_label.setFont(title_font)
        text_title = self.themes["app_color"]["text_title"]
        title_label.setStyleSheet(f"color: {text_title};")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 32)
        bg_three = self.themes["app_color"]["bg_three"]
        bg_two = self.themes["app_color"]["bg_two"]
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {text_title};
                border: none;
                border-radius: 16px;
                font-size: 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {bg_three};
            }}
            QPushButton:pressed {{
                background-color: {bg_two};
            }}
        """)
        close_btn.clicked.connect(dialog.reject)
        title_layout.addWidget(close_btn)
        container_layout.addLayout(title_layout)
        return close_btn
    
    def _create_dialog_message_label(self, message, message_color=None):
        """创建对话框消息标签"""
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        message_label.setFixedWidth(372)
        message_font = QFont()
        message_font.setPointSize(16)
        message_label.setFont(message_font)
        text_color = message_color or self.themes["app_color"]["text_foreground"]
        message_label.setStyleSheet(f"color: {text_color}; padding: 8px 0px;")
        message_label.setMinimumHeight(40)
        message_label.adjustSize()
        return message_label
    
    def _create_dialog_buttons(self, container_layout, dialog, show_cancel=True):
        """创建对话框按钮"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        bg_two = self.themes["app_color"]["bg_two"]
        bg_three = self.themes["app_color"]["bg_three"]
        text_color = self.themes["app_color"]["text_foreground"]
        context_color = self.themes["app_color"]["context_color"]
        context_hover = self.themes["app_color"]["context_hover"]
        context_pressed = self.themes["app_color"]["context_pressed"]
        
        if show_cancel:
            cancel_btn = QPushButton("Cancel")
            cancel_font = QFont()
            cancel_font.setPointSize(16)
            cancel_font.setBold(True)
            cancel_btn.setFont(cancel_font)
            cancel_btn.setFixedSize(120, 45)
            cancel_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_two};
                    color: {text_color};
                    border: 2px solid {bg_three};
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {bg_three};
                    border: 2px solid {context_hover};
                }}
                QPushButton:pressed {{
                    background-color: {bg_two};
                }}
            """)
            cancel_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_btn)
        
        ok_text = "Confirm" if show_cancel else "OK"
        ok_btn = QPushButton(ok_text)
        ok_font = QFont()
        ok_font.setPointSize(16)
        ok_font.setBold(True)
        ok_btn.setFont(ok_font)
        ok_btn.setFixedSize(120, 45)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {context_color};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {context_hover};
            }}
            QPushButton:pressed {{
                background-color: {context_pressed};
            }}
        """)
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        container_layout.addLayout(button_layout)
    
    def _apply_dialog_style(self, dialog, main_container):
        """应用对话框样式和阴影效果"""
        bg_one = self.themes["app_color"]["bg_one"]
        bg_two = self.themes["app_color"]["bg_two"]
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: transparent;
            }}
            QFrame#main_container {{
                background-color: {bg_one};
                border: 1px solid {bg_two};
                border-radius: 12px;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 100))
        main_container.setGraphicsEffect(shadow)
    
    def _center_dialog(self, dialog):
        """居中显示对话框"""
        dialog.move(
            self.main_window.x() + (self.main_window.width() - dialog.width()) // 2,
            self.main_window.y() + (self.main_window.height() - dialog.height()) // 2
        )
    
    def _show_confirm_dialog(self, title, message):
        """
        显示现代化的确认对话框，与主界面风格一致
        
        参数:
            title: 标题
            message: 消息内容
        
        返回:
            bool: True 如果用户点击确认，False 如果用户点击取消
        """
        if not (hasattr(self, 'themes') and self.themes):
            # 基本样式（无主题）
            dialog = QDialog(self.main_window)
            dialog.setWindowFlag(Qt.FramelessWindowHint)
            dialog.setAttribute(Qt.WA_TranslucentBackground)
            dialog.setModal(True)
            dialog.setFixedSize(420, self._calculate_dialog_height(message))
            
            main_container = QFrame(dialog)
            main_container.setObjectName("main_container")
            main_layout = QVBoxLayout(dialog)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.addWidget(main_container)
            
            container_layout = QVBoxLayout(main_container)
            container_layout.setContentsMargins(24, 24, 24, 24)
            container_layout.setSpacing(20)
            
            label = QLabel(message)
            label.setWordWrap(True)
            label.setFixedWidth(372)
            container_layout.addWidget(label)
            
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            container_layout.addWidget(button_box)
            
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #2c313c;
                }
                QFrame#main_container {
                    background-color: #2c313c;
                    border: 1px solid #343b48;
                    border-radius: 12px;
                }
            """)
            self._center_dialog(dialog)
            return dialog.exec() == QDialog.Accepted
        
        # 现代化样式（有主题）
        dialog, main_container, container_layout = self._create_modern_dialog_base(title, message)
        self._create_dialog_title(container_layout, title, dialog)
        
        # 分隔线
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {self.themes['app_color']['bg_three']};")
        container_layout.addWidget(divider)
        
        # 消息内容
        message_label = self._create_dialog_message_label(message)
        container_layout.addWidget(message_label)
        container_layout.addStretch()
        
        # 按钮部分
        self._create_dialog_buttons(container_layout, dialog, show_cancel=True)
        
        # 应用样式
        self._apply_dialog_style(dialog, main_container)
        self._center_dialog(dialog)
        
        return dialog.exec() == QDialog.Accepted
    
    def _get_message_color_by_type(self, message_type):
        """根据消息类型获取颜色"""
        context_color = self.themes["app_color"]["context_color"]
        text_color = self.themes["app_color"]["text_foreground"]
        
        if message_type == "success":
            return self.themes["app_color"].get("green", context_color)
        elif message_type == "warning":
            return self.themes["app_color"].get("yellow", "#ffaa00")
        elif message_type == "error":
            return self.themes["app_color"].get("red", "#ff5555")
        else:
            return text_color
    
    def _calculate_message_dialog_height(self, message, base_height=220, fixed_part=180):
        """计算消息对话框高度（使用更精确的方法）"""
        from PySide6.QtGui import QTextDocument
        message_label_temp = QLabel(message)
        message_label_temp.setWordWrap(True)
        message_label_temp.setFixedWidth(372)
        message_font_temp = QFont()
        message_font_temp.setPointSize(16)
        message_label_temp.setFont(message_font_temp)
        
        doc = QTextDocument()
        doc.setDefaultFont(message_font_temp)
        doc.setTextWidth(372)
        doc.setPlainText(message)
        message_height = int(doc.size().height()) + 20
        message_height = max(message_height, 40)
        return max(base_height, fixed_part + message_height)
    
    def show_modern_message(self, title, message, message_type="info"):
        """
        显示现代化的消息框，与主界面风格一致
        
        参数:
            title: 标题
            message: 消息内容
            message_type: 消息类型 ("info", "success", "warning", "error")
        """
        if not (hasattr(self, 'themes') and self.themes):
            # 基本样式（无主题）
            dialog = QDialog(self.main_window)
            dialog.setWindowFlag(Qt.FramelessWindowHint)
            dialog.setAttribute(Qt.WA_TranslucentBackground)
            dialog.setModal(True)
            dialog.setFixedSize(420, self._calculate_message_dialog_height(message))
            
            main_container = QFrame(dialog)
            main_container.setObjectName("main_container")
            main_layout = QVBoxLayout(dialog)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.addWidget(main_container)
            
            container_layout = QVBoxLayout(main_container)
            container_layout.setContentsMargins(24, 24, 24, 24)
            container_layout.setSpacing(20)
            
            label = QLabel(message)
            label.setWordWrap(True)
            container_layout.addWidget(label)
            
            ok_btn = QPushButton("OK")
            ok_btn.clicked.connect(dialog.accept)
            container_layout.addWidget(ok_btn)
            
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #2c313c;
                }
                QFrame#main_container {
                    background-color: #2c313c;
                    border: 1px solid #343b48;
                    border-radius: 12px;
                }
            """)
            self._center_dialog(dialog)
            dialog.exec()
            return
        
        # 现代化样式（有主题）
        dialog = QDialog(self.main_window)
        dialog.setWindowFlag(Qt.FramelessWindowHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setModal(True)
        dialog.setFixedSize(420, self._calculate_message_dialog_height(message))
        
        main_container = QFrame(dialog)
        main_container.setObjectName("main_container")
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_container)
        
        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(24, 24, 24, 24)
        container_layout.setSpacing(20)
        
        self._create_dialog_title(container_layout, title, dialog)
        
        # 分隔线
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {self.themes['app_color']['bg_three']};")
        container_layout.addWidget(divider)
        
        # 消息内容（带类型颜色）
        message_color = self._get_message_color_by_type(message_type)
        message_label = self._create_dialog_message_label(message, message_color)
        container_layout.addWidget(message_label)
        container_layout.addStretch()
        
        # 按钮部分（只显示OK按钮）
        self._create_dialog_buttons(container_layout, dialog, show_cancel=False)
        
        # 应用样式
        self._apply_dialog_style(dialog, main_container)
        self._center_dialog(dialog)
        
        dialog.exec()
    
    def delete_icon(self, ability_name, icon_path):
        """
        删除图标文件并刷新页面
        
        参数:
            ability_name: 图标名称
            icon_path: 图标文件路径
        """
        # 弹出确认对话框
        reply = QMessageBox.question(
            self.main_window,
            "Confirm Delete",
            f"Are you sure you want to delete icon '{ability_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 删除文件
                if os.path.exists(icon_path):
                    os.remove(icon_path)
                    print(f"已删除图标文件: {icon_path}")
                else:
                    print(f"图标文件不存在: {icon_path}")
                    QMessageBox.warning(
                        self.main_window,
                        "Delete Failed",
                        f"Icon file does not exist: {icon_path}"
                    )
                    return
                
                # 从配置数据中删除对应的快捷键绑定（如果存在）
                if hasattr(self, 'config_data') and ability_name in self.config_data:
                    del self.config_data[ability_name]
                    # 保存更新后的配置（如果子类实现了此方法）
                    if hasattr(self, 'save_config_with_rules'):
                        self.save_config_with_rules()
                
                # 刷新页面，重新加载图标
                self.reload_icons()
                
            except Exception as e:
                print(f"删除图标时发生错误: {e}")
                QMessageBox.critical(
                    self.main_window,
                    "Delete Failed",
                    f"Error deleting icon: {str(e)}"
                )

