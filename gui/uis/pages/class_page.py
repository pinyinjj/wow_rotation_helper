import json
import os
import sys

from PySide6.QtCore import QCoreApplication, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtCore import QSize, QThread, Signal
from PySide6.QtGui import QIcon, Qt, QPixmap, QColor
from PySide6.QtWidgets import QPushButton, QGridLayout, QVBoxLayout, QLabel, QHBoxLayout, QWidget, \
    QMainWindow, QSizePolicy, QDialog, QMessageBox, QInputDialog, QLineEdit
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from gui.core.json_settings import Settings
from gui.core.functions import Functions
from gui.core.json_themes import Themes
from gui.widgets import PyGroupbox, PyPushButton, PyLoggerWindow
from rotation import RotationThread
from .key_binding import KeyBindDialog
from ...widgets.py_dialog import PyDialog
from ...widgets.py_add_icon_dialog import ModernAddIconDialog

current_dir = os.path.dirname(os.path.abspath(__file__))
gui_dir = os.path.join(current_dir, "..", "..")

class Ui_ClassPage(object):
    def __init__(self, main_window: QMainWindow):
        self.main_window = main_window
        self.settings = Settings()
        self.debug = self.settings.items.get("debug", "False").lower() == "true"
        self.selected_class = None
        self.selected_talent = None
        self.selected_class_name = None
        self.selected_talent_name = None
        self.rotation_thread = None
        self.is_running = False

        self.config_data = {}  # 用于存储技能绑定
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "config", "config.json")
        self.config_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "config")
        
        # 用于存储图标widget的字典，key为图标名称，value为icon_widget
        self.icon_widgets = {}  # 存储所有图标widget
        self.current_highlighted_icon = None  # 当前高亮的图标名称
        self.highlight_animations = {}  # 存储高亮动画

    def setupUi(self, page_skills):

        # LOAD THEME COLOR
        # ///////////////////////////////////////////////////////////////
        themes = Themes()
        self.themes = themes.items

        self.page_skills_layout = QVBoxLayout(page_skills)

        # Class Group
        self.class_group = PyGroupbox("Class Selection", self.themes)
        self.class_layout = QGridLayout()
        self.class_layout.setHorizontalSpacing(5)
        self.class_layout.setVerticalSpacing(10)
        self.class_group.setLayout(self.class_layout)
        self.page_skills_layout.addWidget(self.class_group)

        # 创建 Talent Group
        self.talent_group = PyGroupbox("Talent Selection", self.themes)
        self.talent_layout = QGridLayout()
        self.talent_layout.setHorizontalSpacing(5)
        self.talent_layout.setVerticalSpacing(10)
        self.talent_group.setLayout(self.talent_layout)
        self.page_skills_layout.addWidget(self.talent_group)
        self.talent_group.setVisible(False)

        # 创建 Talent Ability Group
        self.talent_ability = PyGroupbox("Talent Abilities", self.themes)
        self.talent_ability_layout = QGridLayout()
        self.talent_ability_layout.setHorizontalSpacing(10)
        self.talent_ability_layout.setVerticalSpacing(10)
        # 设置列宽策略，防止列被压缩
        # 每列最小宽度 = 图标宽度(64) + 按钮宽度(80) + 间距(5) = 149
        min_column_width = 64 + 80 + 5
        for i in range(6):  # 假设最多6列
            self.talent_ability_layout.setColumnMinimumWidth(i, min_column_width)
            self.talent_ability_layout.setColumnStretch(i, 0)  # 不拉伸，保持固定宽度
        self.talent_ability.setLayout(self.talent_ability_layout)
        self.page_skills_layout.addWidget(self.talent_ability)
        self.talent_ability.setVisible(False)

        self.button_layout = QHBoxLayout()
        self.page_skills_layout.addLayout(self.button_layout)

        self.load_button = self.create_button(icon="save_icon.svg")
        self.load_button.setText("Save")
        self.load_button.clicked.connect(self.save_config_with_rules)
        self.button_layout.addWidget(self.load_button)

        self.reload_button = self.create_button(icon="refresh.svg")
        self.reload_button.setText("Reload")
        self.reload_button.clicked.connect(self.reload_icons)
        self.button_layout.addWidget(self.reload_button)

        self.start_button = self.create_button(icon="start.svg")
        self.start_button.setText("Start")
        self.start_button.clicked.connect(self.toggle_start_pause)
        self.button_layout.addWidget(self.start_button)

        class_icon_path = os.path.join(gui_dir, "uis", "icons", "class_icons")
        class_icons = [f for f in os.listdir(class_icon_path) if f.endswith(".tga")]

        for i, icon_filename in enumerate(class_icons):
            class_name = os.path.splitext(icon_filename)[0]
            icon_path = os.path.join(class_icon_path, icon_filename)
            button = self.create_class_button(icon_path, QSize(100, 100), class_name,
                                              lambda _, class_name=class_name: self.load_talent_icons(class_name))
            self.class_layout.addWidget(button, i // 6, i % 6)

        self.adjust_class_icon_spacing()
        # self.adjust_main_window_size()  # 初始加载时调整窗口大小 - 已禁用自动调整窗口大小

        if self.debug:
            self.load_logger_frame()

    def reload_icons(self):
        self.load_ability_icons(self.selected_class_name, self.selected_talent_name)
        print(f'reload for {self.selected_class_name, self.selected_talent_name}')

    def load_logger_frame(self):
        self.log_text_edit = PyLoggerWindow(
            bg_color=self.themes["app_color"]["bg_one"],
            color=self.themes["app_color"]["text_foreground"],
            radius="8px",
            padding="10px",
            font_size=30,
            bg_color_readonly=self.themes["app_color"]["dark_two"],
            hover_color=self.themes["app_color"]["context_hover"]
        )
        self.page_skills_layout.addWidget(self.log_text_edit)  # 将日志框体添加到布局的最下方

        # 重定向标准输出和错误输出到日志窗口
        sys.stdout = self.log_text_edit
        sys.stderr = self.log_text_edit

    def closeEvent(self, event):
        """Restore stdout and stderr on close."""
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        super().closeEvent(event)

    def save_config_with_rules(self):
        """点击加载时，保存所有技能的快捷键到配置文件"""
        # 生成文件名
        class_name = self.selected_class_name if self.selected_class else "unknown_class"
        talent_name = self.selected_talent_name if self.selected_talent else "unknown_talent"

        config_filename = f"{class_name}_{talent_name}.json"
        config_filepath = os.path.join(self.config_folder, config_filename)

        # 加载现有的配置文件内容（如果存在）
        existing_config = {}
        if os.path.exists(config_filepath):
            try:
                with open(config_filepath, 'r', encoding='utf-8') as file:
                    existing_config = json.load(file)
                    print(f"现有配置文件已加载: {config_filepath}")
            except json.JSONDecodeError as e:
                print(f"加载现有配置文件时发生错误: {e}")
                existing_config = {}

        # 遍历天赋技能布局，获取按钮绑定的快捷键
        for i in range(self.talent_ability_layout.count()):
            ability_widget = self.talent_ability_layout.itemAt(i).widget()
            layout = ability_widget.layout()

            if layout:
                button = layout.itemAt(1).widget()  # 获取按钮
                shortcut = button.text().strip()  # 从按钮文本中获取快捷键

                # 从按钮的 toolTip 中获取技能名称
                ability_name = button.toolTip()
                if ability_name and shortcut:
                    existing_config[ability_name] = shortcut.lower()  # 将快捷键转换为小写

        # 将更新后的配置保存到文件
        with open(config_filepath, 'w', encoding='utf-8') as file:
            json.dump(existing_config, file, indent=4, ensure_ascii=False)
            print(f"配置已成功写入到 {config_filepath}")

        # 打印收集到的配置数据
        print(f"更新后的配置数据: {existing_config}")

    def load_latest_config(self):
        if not self.selected_class_name or not self.selected_talent_name:
            return

        prefix = f"{self.selected_class_name}_{self.selected_talent_name}"

        if not os.path.exists(self.config_folder):
            os.makedirs(self.config_folder)

        try:
            config_files = [f for f in os.listdir(self.config_folder) if f.startswith(prefix) and f.endswith('.json')]
        except Exception:
            return

        if config_files:
            latest_filepath = os.path.join(self.config_folder, config_files[0])
            self.load_config_from_file(latest_filepath)
            return latest_filepath
        else:
            empty_config = {}
            default_config_filename = f"{prefix}.json"
            default_config_filepath = os.path.join(self.config_folder, default_config_filename)

            try:
                with open(default_config_filepath, 'w') as config_file:
                    json.dump(empty_config, config_file, indent=4)
            except Exception:
                return

            self.load_config_from_file(default_config_filepath)
            return default_config_filepath

    def load_config_from_file(self, filepath):
        """从配置文件中加载绑定并将输入框转换为按钮"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                self.config_data = json.load(file)
                print(f"加载配置文件 {filepath} 成功: {self.config_data}")


        except FileNotFoundError:
            print(f"配置文件 {filepath} 未找到")
        except json.JSONDecodeError as e:
            print(f"解析配置文件错误: {e}")

    def format_shortcut(self, shortcut):
        """格式化按键绑定，F1-F10 全大写，其他按键首字母大写"""
        if shortcut.startswith("F") and shortcut[1:].isdigit() and 1 <= int(shortcut[1:]) <= 10:
            return shortcut.upper()  # F1-F10 全大写
        else:
            return shortcut.capitalize()  # 其他按键首字母大写

    def toggle_start_pause(self):
        """Start or stop the RotationThread."""
        if not self.selected_class and self.selected_talent:
            print(f"Found unknown {self.selected_class} + {self.selected_talent}.")
            return

        if not self.is_running:
            # Starting the rotation thread
            print("QT Starting RotationThread...")

            # Load the latest configuration file
            config_filepath = self.load_latest_config()

            if not config_filepath:
                print("Configuration file not found, unable to start the rotation thread.")
                return

            # Ensure RotationThread is not already running
            if not self.rotation_thread or not self.rotation_thread.isRunning():
                # Create and start a new RotationThread
                print("Creating and starting new RotationThread.")
                self.rotation_thread = RotationThread(
                    config_file='rotation_config.yaml',
                    keybind_file=config_filepath,
                    class_name=self.selected_class_name,
                    talent_name=self.selected_talent_name,
                    game_version='retail'
                )
                self.rotation_thread.finished.connect(self.on_thread_finished)
                # Connect icon matched signal to highlight handler
                self.rotation_thread.icon_matched.connect(self.on_icon_matched)

                self.rotation_thread.start()  # Start the thread
                print("RotationThread started.")

                # Update button appearance after successfully starting the thread
                self.start_button.setText("Stop")
                self.start_button.setIcon(QIcon(Functions.set_svg_icon("pause.svg")))
                self.is_running = True
            else:
                print("RotationThread is already running.")

        else:
            # Stopping the thread
            print("QT stopping RotationThread...")

            # Ensure the RotationThread is running before trying to stop it
            if self.rotation_thread and self.rotation_thread.isRunning():
                self.rotation_thread.stop()  # Stop the RotationThread
                self.rotation_thread.wait()  # Wait for the thread to finish
                # clean_up() will be called in on_thread_finished() when finished signal is emitted

                # Update button appearance after the thread has stopped
                self.start_button.setText("Start")
                self.start_button.setIcon(QIcon(Functions.set_svg_icon("start.svg")))
                self.is_running = False
            else:
                print("RotationThread is not running or already stopped.")

    def on_thread_finished(self):
        """Handle thread completion and clean up."""
        print("RotationThread finished.")
        if self.rotation_thread:
            self.rotation_thread.clean_up()  # Ensure everything is cleaned up
            self.rotation_thread = None  # Remove reference to the thread
        self.start_button.setText("Start")
        self.is_running = False

    def create_button(self, size=40, icon=None):
        button = QPushButton()
        if icon:
            icon_path = Functions.set_svg_icon(icon)
            button.setIcon(QIcon(icon_path))

        # 设置按钮为方形，宽度增加
        button.setFixedSize(size + 100, size)
        button.setIconSize(QSize(size - 10, size - 10))  # 图标比按钮稍小一些

        # 设置按钮的样式，确保所有状态的颜色和样式正确生效
        button.setStyleSheet("""
            QPushButton {
                background-color: #343b48;  /* 默认背景颜色 */
                border-radius: 8px;  /* 圆角 */
                color: #c3ccdf;  /* 默认图标颜色 */
                border: 2px solid #343b48;  /* 默认边框颜色 */
                padding: 5px;  /* 确保内容不会紧贴边缘 */
            }
            QPushButton:hover {
                background-color: #3c4454;  /* 悬浮时背景颜色 */
                color: #dce1ec;  /* 悬浮时图标颜色 */
                border-color: #3c4454;  /* 悬浮时边框颜色 */
            }
            QPushButton:pressed {
                background-color: #2c313c;  /* 点击时背景颜色 */
                color: #edf0f5;  /* 点击时图标颜色 */
                border-color: #2c313c;  /* 点击时边框颜色 */
            }
            QPushButton:checked {
                background-color: #1b1e23;  /* 激活状态背景颜色 */
                color: #f5f6f9;  /* 激活状态图标颜色 */
                border-color: #568af2;  /* 激活状态边框颜色 */
            }
        """)

        return button

    def adjust_class_icon_spacing(self, spacing_factor=1):
        window_width = self.main_window.width()
        columns = 6
        icon_size = 64
        total_padding = window_width - (columns * icon_size)
        spacing = total_padding // (columns + 1) * spacing_factor
        # 限制最大间距为5，确保class图标间距不会太大
        spacing = min(spacing, 5)
        self.class_layout.setHorizontalSpacing(spacing)

    def create_class_button(self, icon_path, icon_size, class_name, on_click_callback):
        class_button = QPushButton()
        class_button.setProperty("name", class_name)
        icon = QIcon(icon_path)
        class_button.setIcon(icon)
        class_button.setIconSize(QSize(icon_size.width() - 10, icon_size.height() - 10))
        class_button.setFixedSize(icon_size.width(), icon_size.height())
        class_button.setStyleSheet(self.get_button_style(selected=False))
        class_button.clicked.connect(lambda _: self.on_class_button_clicked(class_button, on_click_callback))
        return class_button

    def on_class_button_clicked(self, class_button, on_click_callback):
        if self.selected_talent:
            self.selected_talent = None
            self.selected_talent_name = None

        if self.selected_class and self.selected_class != class_button:
            self.selected_class.setStyleSheet(self.get_button_style(selected=False))
            self.clear_layout(self.talent_layout)
            self.clear_layout(self.talent_ability_layout)
            self.talent_group.setVisible(False)
            self.talent_ability.setVisible(False)

        self.selected_class = class_button
        self.selected_class_name = class_button.property("name")
        class_button.setStyleSheet(self.get_button_style(selected=True))
        on_click_callback(class_button)

        self.talent_group.setVisible(True)

    def relayout_for_talent_display(self):
        self.class_layout.setVerticalSpacing(10)
        self.adjust_class_icon_spacing()
        # self.adjust_main_window_size()  # 已禁用自动调整窗口大小

    def on_talent_button_clicked(self, button, talent_name, class_name):
        print(f"Button clicked: {button}, Talent: {talent_name}, Class: {class_name}")

        if self.selected_talent and self.selected_talent != button:
            print("Deselecting previous talent button.")
            self.selected_talent.setStyleSheet(self.get_button_style(selected=False))

        # 记录选中的按钮
        self.selected_talent = button
        print(f"Selected talent button: {self.selected_talent}")

        # 更新按钮样式
        button.setStyleSheet(self.get_button_style(selected=True))
        # print("Button style updated.")

        # 清空天赋能力布局
        # print("Clearing talent ability layout.")
        self.clear_layout(self.talent_ability_layout)

        # 更新选中的天赋名称
        self.selected_talent_name = button.property("name")
        print(f"Selected talent name: {self.selected_talent_name}")

        # 隐藏天赋能力部分
        self.talent_ability.setVisible(False)
        # print("Talent ability hidden.")

        # 在选择天赋后加载最新的配置文件
        # print("Loading latest config...")
        self.load_latest_config()  # 加载最新配置
        # print("Config loaded.")

        # 加载能力图标
        print(f"Loading ability icons for Class: {class_name}, Talent: {talent_name}")
        self.load_ability_icons(class_name, talent_name)
        # print("Ability icons loaded.")

        # 显示天赋能力
        self.talent_ability.setVisible(True)
        # print("Talent ability visible.")

        # 调整布局以显示能力
        # print("Relayout for ability display.")
        self.relayout_for_ability_display()
        # print("Relayout complete.")

    def clear_layout(self, layout):
        # 清理布局中的所有小部件
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

    def load_ability_icons(self, class_name, talent_name):
        talent_dir = os.path.join(gui_dir, "uis", "icons", "talent_icons", class_name, talent_name.lower())
        self.load_abilities(self.talent_ability_layout, talent_dir)
        self.talent_ability.setVisible(True)
        # 根据abilities数量调整窗口高度
        self.adjust_window_height_for_abilities()

    def relayout_for_ability_display(self):
        # 重新布局并显示技能组
        self.class_layout.setVerticalSpacing(10)
        self.talent_layout.setVerticalSpacing(10)
        self.adjust_class_icon_spacing()
        # self.adjust_main_window_size()  # 已禁用自动调整窗口大小

    def create_talent_button(self, icon_path, icon_size, talent_name, class_name):
        # Create the QPushButton
        talent_button = QPushButton()
        print(f"create_talent_button {talent_name}")

        # Set a property for identifying the button
        talent_button.setProperty("name", talent_name)

        # Load the image using QPixmap
        pixmap = QPixmap(icon_path)

        # Scale the pixmap to fit the button size, keeping aspect ratio
        scaled_pixmap = pixmap.scaled(
            icon_size.width() - 10,
            icon_size.height() - 10,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        # Create a QIcon from the scaled QPixmap and set it on the button
        icon = QIcon(scaled_pixmap)
        talent_button.setIcon(icon)
        talent_button.setIconSize(QSize(icon_size.width() - 10, icon_size.height() - 10))

        # Set the button's fixed size
        talent_button.setFixedSize(icon_size.width(), icon_size.height())

        # Apply the stylesheet
        talent_button.setStyleSheet(self.get_button_style(selected=False))

        # Connect the button click signal to the appropriate slot
        talent_button.clicked.connect(
            lambda _: self.on_talent_button_clicked(talent_button, talent_name, class_name)
        )

        return talent_button

    def load_talent_icons(self, class_name):
        # Clear the existing icons in the layout
        for i in reversed(range(self.talent_layout.count())):
            self.talent_layout.itemAt(i).widget().setParent(None)

        # Define the path to the icons folder
        talent_icon_path = os.path.join(gui_dir, "uis", "icons", "talent_icons", class_name)

        # Include multiple image extensions
        valid_extensions = {".tga", ".png", ".jpg", ".jpeg", ".bmp"}
        talent_icons = [f for f in os.listdir(talent_icon_path) if os.path.splitext(f)[1].lower() in valid_extensions]

        # Iterate over the icons and create buttons
        for i, talent_icon in enumerate(talent_icons):
            icon_path = os.path.join(talent_icon_path, talent_icon)
            talent_name = os.path.splitext(talent_icon)[0].lower()
            button = self.create_talent_button(icon_path, QSize(128, 128), talent_name, class_name)
            self.talent_layout.addWidget(button, i // 4, i % 4)

    def load_abilities_from_directory(self, directory):
        abilities = []
        # 定义支持的图像文件扩展名
        supported_extensions = ['.tga', '.png', '.jpg', '.jpeg']

        if not os.path.exists(directory):
            return abilities

        for filename in os.listdir(directory):
            # 检查文件的扩展名是否在支持的列表中
            if any(filename.lower().endswith(ext) for ext in supported_extensions):
                abilities.append(os.path.join(directory, filename))

        return abilities

    def adjust_main_window_size(self):
        """动态调整窗口大小以容纳所有图标，确保无压缩"""
        from PySide6.QtCore import QTimer
        
        # 使用QTimer延迟执行，确保布局已完成
        def calculate_and_resize():
            # 暂时禁用窗口更新
            self.main_window.setUpdatesEnabled(False)

            # 定义常量
            CLASS_COLUMNS = 6
            TALENT_COLUMNS = 4
            ABILITY_COLUMNS = 6
            
            CLASS_ICON_SIZE = 100  # 职业图标大小
            TALENT_ICON_SIZE = 128  # 天赋图标大小
            ABILITY_ICON_SIZE = 64  # 技能图标高度
            ABILITY_BUTTON_WIDTH = 120  # 技能按钮宽度
            ABILITY_BUTTON_HEIGHT = 64  # 技能按钮高度
            ABILITY_WIDGET_WIDTH = ABILITY_ICON_SIZE + ABILITY_BUTTON_WIDTH + 5  # 图标+按钮+间距
            ABILITY_WIDGET_HEIGHT = max(ABILITY_ICON_SIZE, ABILITY_BUTTON_HEIGHT)  # 取较大值
            
            HORIZONTAL_SPACING = 15
            VERTICAL_SPACING = 15
            GROUPBOX_HEADER_HEIGHT = 50  # Groupbox标题栏高度（增加以容纳标题和边框）
            GROUPBOX_BORDER = 4  # Groupbox边框宽度
            GROUPBOX_MARGIN = 15  # Groupbox内边距
            BUTTON_BAR_HEIGHT = 70  # 按钮栏高度（增加缓冲）
            PAGE_MARGIN = 10  # 页面边距（从main_pages.ui获取）
            EXTRA_BUFFER = 40  # 额外缓冲空间，防止压缩

            # 计算每个section的行数
            class_count = self.class_layout.count()
            class_rows = (class_count + CLASS_COLUMNS - 1) // CLASS_COLUMNS if class_count > 0 else 0
            
            talent_count = self.talent_layout.count() if self.talent_group.isVisible() else 0
            talent_rows = (talent_count + TALENT_COLUMNS - 1) // TALENT_COLUMNS if talent_count > 0 else 0
            
            ability_count = self.talent_ability_layout.count() if self.talent_ability.isVisible() else 0
            ability_rows = (ability_count + ABILITY_COLUMNS - 1) // ABILITY_COLUMNS if ability_count > 0 else 0

            # 计算宽度 - 取所有可见section的最大宽度
            widths = []
            
            if class_count > 0:
                # 职业图标宽度：列数 * 图标大小 + (列数+1) * 间距 + Groupbox内边距
                # 注意：6列需要7个间距（左右各一个，中间5个）
                class_width = CLASS_COLUMNS * CLASS_ICON_SIZE + (CLASS_COLUMNS + 1) * HORIZONTAL_SPACING
                class_width += GROUPBOX_MARGIN * 2 + GROUPBOX_BORDER * 2
                # 增加额外的安全边距，确保所有图标可见
                # 考虑中央widget边距(10px*2) + 其他可能的边距
                class_width += 100  # 额外的安全边距，确保第6个图标完全可见
                widths.append(class_width)
                print(f"Class width calculation: {CLASS_COLUMNS} icons * {CLASS_ICON_SIZE}px = {CLASS_COLUMNS * CLASS_ICON_SIZE}px")
                print(f"Spacing: {(CLASS_COLUMNS + 1)} * {HORIZONTAL_SPACING}px = {(CLASS_COLUMNS + 1) * HORIZONTAL_SPACING}px")
                print(f"Groupbox margins: {GROUPBOX_MARGIN * 2}px, borders: {GROUPBOX_BORDER * 2}px")
                print(f"Total class_width: {class_width}px")
            
            if talent_count > 0:
                # 天赋图标宽度
                talent_width = TALENT_COLUMNS * TALENT_ICON_SIZE + (TALENT_COLUMNS + 1) * HORIZONTAL_SPACING
                talent_width += GROUPBOX_MARGIN * 2 + GROUPBOX_BORDER * 2
                widths.append(talent_width)
            
            if ability_count > 0:
                # 技能图标宽度：列数 * widget宽度 + (列数+1) * 间距 + Groupbox内边距
                ability_width = ABILITY_COLUMNS * ABILITY_WIDGET_WIDTH + (ABILITY_COLUMNS + 1) * HORIZONTAL_SPACING
                ability_width += GROUPBOX_MARGIN * 2 + GROUPBOX_BORDER * 2
                widths.append(ability_width)
            
            # 如果没有可见内容，使用默认宽度
            content_width = max(widths) if widths else 800
            # 注意：PAGE_MARGIN已经在class_width计算中考虑了，这里不需要再加
            # content_width += PAGE_MARGIN * 2  # 左右页面边距（已在class_width中考虑）
            content_width += EXTRA_BUFFER  # 额外缓冲
            content_width += 30  # 额外的右侧缓冲，确保最右侧图标完全可见
            # 注意：class_width中已经包含了100px的额外缓冲，这里不需要再加太多
            print(f"Content width before left menu: {content_width}px")
            
            # 获取左侧菜单宽度（如果存在）
            left_menu_width = 0
            try:
                # 尝试获取左侧菜单框架的宽度
                if hasattr(self.main_window, 'ui') and hasattr(self.main_window.ui, 'left_menu_frame'):
                    left_menu_width = self.main_window.ui.left_menu_frame.width()
                    if left_menu_width == 0:
                        # 如果宽度为0，可能菜单被隐藏，使用settings中的最大值
                        settings = Settings()
                        left_menu_maximum = settings.items.get("lef_menu_size", {}).get("maximum", 240)
                        left_menu_margin = settings.items.get("left_menu_content_margins", 3)
                        left_menu_width = left_menu_maximum + (left_menu_margin * 2)
                else:
                    # 从settings获取默认值
                    settings = Settings()
                    left_menu_maximum = settings.items.get("lef_menu_size", {}).get("maximum", 240)
                    left_menu_margin = settings.items.get("left_menu_content_margins", 3)
                    left_menu_width = left_menu_maximum + (left_menu_margin * 2)
            except Exception as e:
                # 如果获取失败，使用默认值
                settings = Settings()
                left_menu_maximum = settings.items.get("lef_menu_size", {}).get("maximum", 240)
                left_menu_margin = settings.items.get("left_menu_content_margins", 3)
                left_menu_width = left_menu_maximum + (left_menu_margin * 2)
            
            # 总窗口宽度 = 左侧菜单宽度 + 内容区域宽度
            total_width = left_menu_width + content_width
            print(f"Left menu width: {left_menu_width}px")
            print(f"Total window width: {total_width}px (left_menu: {left_menu_width}px + content: {content_width}px)")
            
            # 计算高度
            total_height = PAGE_MARGIN * 2  # 上下页面边距
            
            if class_count > 0:
                total_height += GROUPBOX_HEADER_HEIGHT  # Class Group标题
                total_height += GROUPBOX_MARGIN * 2  # Groupbox上下内边距
                total_height += GROUPBOX_BORDER * 2  # Groupbox上下边框
                total_height += class_rows * CLASS_ICON_SIZE
                if class_rows > 0:
                    total_height += (class_rows + 1) * VERTICAL_SPACING
            
            if talent_count > 0:
                total_height += GROUPBOX_HEADER_HEIGHT  # Talent Group标题
                total_height += GROUPBOX_MARGIN * 2  # Groupbox上下内边距
                total_height += GROUPBOX_BORDER * 2  # Groupbox上下边框
                total_height += talent_rows * TALENT_ICON_SIZE
                if talent_rows > 0:
                    total_height += (talent_rows + 1) * VERTICAL_SPACING
            
            if ability_count > 0:
                total_height += GROUPBOX_HEADER_HEIGHT  # Talent Ability Group标题
                total_height += GROUPBOX_MARGIN * 2  # Groupbox上下内边距
                total_height += GROUPBOX_BORDER * 2  # Groupbox上下边框
                total_height += ability_rows * ABILITY_WIDGET_HEIGHT
                if ability_rows > 0:
                    total_height += (ability_rows + 1) * VERTICAL_SPACING
            
            # 按钮栏高度
            total_height += BUTTON_BAR_HEIGHT
            total_height += EXTRA_BUFFER  # 额外缓冲
            
            # 确保窗口足够大，不要设置最大尺寸限制
            self.main_window.setMinimumSize(int(total_width), int(total_height))
            self.main_window.setMaximumSize(16777215, 16777215)  # 移除最大尺寸限制

            # 调整窗口大小
            print(f"Resized window to: {int(total_width)} x {int(total_height)} (Class: {class_count}, Talent: {talent_count}, Ability: {ability_count})")
            self.main_window.resize(int(total_width), int(total_height))

            # 恢复窗口更新
            self.main_window.setUpdatesEnabled(True)
        
        # 延迟执行以确保布局完成
        QTimer.singleShot(100, calculate_and_resize)

    def adjust_window_height_for_abilities(self):
        """根据talent abilities的数量调整窗口高度，确保所有图标完整显示"""
        from PySide6.QtCore import QTimer
        
        def calculate_and_resize():
            # 定义常量
            ABILITY_COLUMNS = 6
            ABILITY_WIDGET_HEIGHT = 64  # 技能widget高度
            VERTICAL_SPACING = 10  # 垂直间距
            GROUPBOX_HEADER_HEIGHT = 50  # Groupbox标题栏高度
            GROUPBOX_MARGIN = 15  # Groupbox内边距
            GROUPBOX_BORDER = 4  # Groupbox边框宽度
            BUTTON_BAR_HEIGHT = 70  # 按钮栏高度
            PAGE_MARGIN = 10  # 页面边距
            EXTRA_BUFFER = 40  # 额外缓冲空间
            
            # 计算abilities的数量和行数
            ability_count = self.talent_ability_layout.count() if self.talent_ability.isVisible() else 0
            ability_rows = (ability_count + ABILITY_COLUMNS - 1) // ABILITY_COLUMNS if ability_count > 0 else 0
            
            # 获取当前窗口尺寸
            current_width = self.main_window.width()
            current_height = self.main_window.height()
            
            # 计算需要的高度
            # 基础高度：标题栏 + 按钮栏 + 页面边距
            base_height = 40 + BUTTON_BAR_HEIGHT + PAGE_MARGIN * 2  # 标题栏40 + 按钮栏70 + 页面边距
            
            # Class Selection部分高度（如果可见）
            class_height = 0
            if self.class_group.isVisible():
                class_count = self.class_layout.count()
                class_rows = (class_count + 6 - 1) // 6 if class_count > 0 else 0
                class_height = GROUPBOX_HEADER_HEIGHT + GROUPBOX_MARGIN * 2 + GROUPBOX_BORDER * 2
                if class_rows > 0:
                    class_height += class_rows * 100  # CLASS_ICON_SIZE = 100
                    class_height += (class_rows + 1) * VERTICAL_SPACING
            
            # Talent Selection部分高度（如果可见）
            talent_height = 0
            if self.talent_group.isVisible():
                talent_count = self.talent_layout.count()
                talent_rows = (talent_count + 4 - 1) // 4 if talent_count > 0 else 0
                talent_height = GROUPBOX_HEADER_HEIGHT + GROUPBOX_MARGIN * 2 + GROUPBOX_BORDER * 2
                if talent_rows > 0:
                    talent_height += talent_rows * 128  # TALENT_ICON_SIZE = 128
                    talent_height += (talent_rows + 1) * VERTICAL_SPACING
            
            # Talent Abilities部分高度
            ability_height = 0
            if ability_count > 0:
                ability_height = GROUPBOX_HEADER_HEIGHT + GROUPBOX_MARGIN * 2 + GROUPBOX_BORDER * 2
                if ability_rows > 0:
                    ability_height += ability_rows * ABILITY_WIDGET_HEIGHT
                    ability_height += (ability_rows + 1) * VERTICAL_SPACING
            
            # 计算总高度
            total_height = base_height + class_height + talent_height + ability_height + EXTRA_BUFFER
            
            # 确保高度不小于当前高度（只增加，不减少）
            if total_height > current_height:
                print(f"调整窗口高度: {current_height} -> {int(total_height)} (abilities: {ability_count}, rows: {ability_rows})")
                self.main_window.resize(current_width, int(total_height))
                # 更新最小高度
                min_width, min_height = self.main_window.minimumSize().width(), self.main_window.minimumSize().height()
                self.main_window.setMinimumSize(min_width, int(total_height))
        
        # 延迟执行以确保布局完成
        QTimer.singleShot(150, calculate_and_resize)

    def get_button_style(self, selected):
        if selected:
            return """
            QPushButton {
                border: 2px solid #FFDD44;
                background-color: #444;
                border-radius: 32px;
            }
            QPushButton:hover {
                background-color: #0000FF;
            }
            """
        else:
            return """
            QPushButton {
                border: 2px solid #000;
                background-color: #000;
                border-radius: 32px;
            }
            QPushButton:hover {
                background-color: #0000FF;
            }
            """

    def load_abilities(self, layout, directory, columns=6):
        """加载技能并创建按钮绑定"""

        # Clear existing items in the layout and icon widgets dict
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Clear icon widgets dictionary and remove any highlights
        for icon_name in list(self.icon_widgets.keys()):
            if icon_name in self.highlight_animations:
                self.remove_highlight(icon_name)
        self.icon_widgets.clear()
        self.current_highlighted_icon = None

        # Load abilities from the specified directory
        abilities = self.load_abilities_from_directory(directory)

        row = 0
        col = 0

        def create_icon_widget(icon_path, tooltip_text):
            """Creates a widget with an icon and sets up layout."""
            icon_label = QLabel()
            icon_label.setFixedSize(64, 64)
            icon_label.setScaledContents(True)

            try:
                icon_label.setPixmap(QIcon(icon_path).pixmap(64, 64))
            except Exception as e:
                print(f"加载图标错误: {e}")
                icon_label.setText("No Icon")

            icon_label.setToolTip(tooltip_text)

            icon_layout = QVBoxLayout()
            icon_layout.addWidget(icon_label)

            icon_widget = QWidget()
            icon_widget.setLayout(icon_layout)
            icon_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            return icon_widget

        for i, icon_path in enumerate(abilities):
            ability_name = os.path.splitext(os.path.basename(icon_path))[0]

            # Create icon widget for each ability
            icon_widget = create_icon_widget(icon_path, ability_name)
            
            # Store icon widget in dictionary for highlighting
            self.icon_widgets[ability_name] = icon_widget

            # Create binding button
            binding_button = self.create_binding_button(ability_name)

            # Apply configuration if binding exists
            if ability_name in self.config_data:
                shortcut = self.config_data[ability_name]
                formatted_shortcut = self.format_shortcut(shortcut)  # 使用新方法格式化
                binding_button.setText(formatted_shortcut)  # 显示格式化后的文本

            # Setup the ability layout
            ability_layout = QHBoxLayout()
            ability_layout.setAlignment(Qt.AlignLeft)
            ability_layout.setSpacing(5)
            ability_layout.addWidget(icon_widget)
            ability_layout.addWidget(binding_button)

            # Wrap ability layout in a widget
            ability_widget = QWidget()
            ability_widget.setLayout(ability_layout)
            # 设置固定尺寸策略，防止被压缩
            ability_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            # 设置最小尺寸，确保图标和按钮有足够空间
            ability_widget.setMinimumSize(64 + 80 + 5, 64)  # 图标宽度 + 按钮宽度 + 间距

            layout.addWidget(ability_widget, row, col)

            # Manage grid positioning
            col += 1
            if col == columns:
                col = 0
                row += 1

        layout.addWidget(self.create_add_icon_widget("icon_search.svg"), row, col)

    def create_add_icon_widget(self, icon='icon_heart.svg'):
        """Creates a widget with an empty icon placeholder and an 'Add Icon' button."""

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
        add_icon_button.setText("Add")

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

        # Create button with custom styling
        add_icon_button = PyPushButton(
            text="Add Icon",
            radius=8,
            color=self.themes["app_color"]["white"],
            bg_color=self.themes["app_color"]["bg_one"],
            bg_color_hover=self.themes["app_color"]["context_hover"],
            bg_color_pressed=self.themes["app_color"]["context_pressed"],
            font_size=20
        )

        add_icon_button.setFixedHeight(64)
        add_icon_button.setFixedWidth(80)
        add_icon_button.setToolTip("Add a new icon")

        # Connect button click to open the dialog
        add_icon_button.clicked.connect(self.show_add_icon_dialog)
        print("Add Icon button setup complete.")  # Debug: Confirm setup complete

        return add_icon_button

    def create_binding_button(self, ability_name):
        """创建用于按键绑定的按钮，并设置样式"""
        button = PyPushButton(
            text="",
            radius=8,
            color=self.themes["app_color"]["white"],
            bg_color=self.themes["app_color"]["bg_one"],
            bg_color_hover=self.themes["app_color"]["context_hover"],
            bg_color_pressed=self.themes["app_color"]["context_pressed"],
            font_size=30
        )

        button.setFixedHeight(64)
        button.setFixedWidth(80)
        button.setToolTip(ability_name)
        # 设置文本居中对齐
        current_style = button.styleSheet()
        button.setStyleSheet(current_style + "text-align: center; padding-left: 0px; padding-right: 0px;")

        def on_button_clicked():
            """点击按钮后打开按键绑定对话框"""
            dialog = KeyBindDialog(self.main_window)
            if dialog.exec() == QDialog.Accepted:

                key_sequence = dialog.key_sequence
                if key_sequence:
                    formatted_shortcut = self.format_shortcut(key_sequence)
                    button.setText(formatted_shortcut)
                    self.config_data[ability_name] = key_sequence

        button.clicked.connect(on_button_clicked)

        return button

    def on_icon_matched(self, icon_name):
        """Handle icon matched signal - highlight the matched icon"""
        if icon_name in self.icon_widgets:
            # Remove highlight from previous icon
            if self.current_highlighted_icon and self.current_highlighted_icon != icon_name:
                self.remove_highlight(self.current_highlighted_icon)
            
            # Highlight the new icon
            if self.current_highlighted_icon != icon_name:
                self.highlight_icon(icon_name)
                self.current_highlighted_icon = icon_name
    
    def highlight_icon(self, icon_name):
        """Add modern flash highlight effect to an icon"""
        if icon_name not in self.icon_widgets:
            return
        
        icon_widget = self.icon_widgets[icon_name]
        
        # Remove any existing highlight animation
        if icon_name in self.highlight_animations:
            self.remove_highlight(icon_name)
        
        # Create glow shadow effect with bright cyan color
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(20)
        shadow_effect.setColor(QColor(0, 255, 255, 255))  # Bright cyan glow
        shadow_effect.setOffset(0, 0)
        icon_widget.setGraphicsEffect(shadow_effect)
        
        # Create pulsing animation for the glow (blur radius animation)
        animation = QPropertyAnimation(shadow_effect, b"blurRadius")
        animation.setDuration(800)  # 0.8 second cycle for smooth pulse
        animation.setStartValue(15)
        animation.setEndValue(35)
        animation.setEasingCurve(QEasingCurve.InOutSine)
        animation.setLoopCount(-1)  # Infinite loop
        
        # Store animations
        self.highlight_animations[icon_name] = {
            'shadow': shadow_effect,
            'blur_animation': animation
        }
        
        # Start animation
        animation.start()
    
    def remove_highlight(self, icon_name):
        """Remove highlight effect from an icon"""
        if icon_name not in self.highlight_animations:
            return
        
        animations = self.highlight_animations[icon_name]
        
        # Stop animations
        if 'blur_animation' in animations:
            animations['blur_animation'].stop()
        
        # Remove graphics effect
        if icon_name in self.icon_widgets:
            self.icon_widgets[icon_name].setGraphicsEffect(None)
        
        # Remove from animations dict
        del self.highlight_animations[icon_name]
        
        if self.current_highlighted_icon == icon_name:
            self.current_highlighted_icon = None

    def retranslateUi(self, page_class):
        page_class.setWindowTitle(QCoreApplication.translate("ClassPage", "Class Page", None))

