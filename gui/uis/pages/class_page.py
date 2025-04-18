import json
import os
import sys

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, Qt, QPixmap
from PySide6.QtWidgets import QPushButton, QGridLayout, QVBoxLayout, QLabel, QHBoxLayout, QWidget, \
    QMainWindow, QSizePolicy, QDialog, QMessageBox, QInputDialog, QLineEdit
from gui.core.json_settings import Settings
from gui.core.functions import Functions
from gui.core.json_themes import Themes
from gui.widgets import PyGroupbox, PyPushButton, PyLoggerWindow
from rotation import RotationThread
from .key_binding import KeyBindDialog
from ...widgets.py_dialog import PyDialog

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

    def setupUi(self, page_skills):

        # LOAD THEME COLOR
        # ///////////////////////////////////////////////////////////////
        themes = Themes()
        self.themes = themes.items

        self.page_skills_layout = QVBoxLayout(page_skills)

        # Class Group
        self.class_group = PyGroupbox("Class Selection", self.themes)
        self.class_layout = QGridLayout()
        self.class_group.setLayout(self.class_layout)
        self.page_skills_layout.addWidget(self.class_group)

        # 创建 Talent Group
        self.talent_group = PyGroupbox("Talent Selection", self.themes)
        self.talent_layout = QGridLayout()
        self.talent_group.setLayout(self.talent_layout)
        self.page_skills_layout.addWidget(self.talent_group)
        self.talent_group.setVisible(False)

        # 创建 Talent Ability Group
        self.talent_ability = PyGroupbox("Talent Abilities", self.themes)
        self.talent_ability_layout = QGridLayout()
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
                self.rotation_thread.clean_up()  # Ensure cleanup of RotationHelper instance
                self.rotation_thread.wait()  # Wait for the thread to finish

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
        self.adjust_main_window_size()

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
        self.adjust_main_window_size()

    def relayout_for_ability_display(self):
        # 重新布局并显示技能组
        self.class_layout.setVerticalSpacing(10)
        self.talent_layout.setVerticalSpacing(10)
        self.adjust_class_icon_spacing()
        self.adjust_main_window_size()

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
        # 暂时禁用窗口更新
        self.main_window.setUpdatesEnabled(False)

        # 计算窗口大小逻辑
        class_icon_rows = (self.class_layout.count() + 5) // 6
        talent_icon_rows = (self.talent_layout.count() + 3) // 4
        talent_ability_rows = (self.talent_ability_layout.count() + 5) // 4

        icon_size = 64
        row_spacing = 10

        total_height = (
                (class_icon_rows + talent_icon_rows + talent_ability_rows)
                * (icon_size + row_spacing)
                + 200  # 额外缓冲空间
        )

        total_width_class = self.class_layout.count() * (icon_size + row_spacing) // 6
        total_width_talent = self.talent_layout.count() * (icon_size + row_spacing) // 4
        total_width_talent_ability = self.talent_ability_layout.count() * (icon_size + row_spacing) // 4

        total_width = max(total_width_class, total_width_talent, total_width_talent_ability)

        max_width = 1200
        max_height = 800

        total_width = min(total_width, max_width)
        total_height = min(total_height, max_height)

        self.main_window.setMinimumSize(0, 0)

        # 调整窗口大小
        print(f"Resized window to: {int(total_width)} x {int(total_height)}")
        self.main_window.resize(int(total_width), int(total_height))

        # 恢复窗口更新
        self.main_window.setUpdatesEnabled(True)

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

        # Clear existing items in the layout
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

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
        add_icon_button.setText("Add Icon")

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
        """Displays a custom dialog with fields for entering IDs."""

        # Create the dialog
        dialog = PyDialog()

        # Access the dialog's layout and add input fields and buttons
        layout = dialog.layout()

        # Input fields for Skill ID, Trinket ID, and Consumable ID
        skill_id_label = QLabel("Spell ID:")
        skill_id_input = QLineEdit()
        trinket_id_label = QLabel("Trinket ID:")
        trinket_id_input = QLineEdit()
        consumable_id_label = QLabel("Consumable ID:")
        consumable_id_input = QLineEdit()

        layout.addWidget(skill_id_label)
        layout.addWidget(skill_id_input)
        layout.addWidget(trinket_id_label)
        layout.addWidget(trinket_id_input)
        layout.addWidget(consumable_id_label)
        layout.addWidget(consumable_id_input)

        # Buttons for OK and Cancel
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Connect buttons to handle dialog response
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        # Display dialog and handle accepted action
        if dialog.exec() == QDialog.Accepted:
            skill_id = skill_id_input.text().strip()
            trinket_id = trinket_id_input.text().strip()
            consumable_id = consumable_id_input.text().strip()

            # Process inputs if Skill ID is provided
            if skill_id:
                try:
                    # Attempt to download the icon
                    status = Functions.download_icon(spell_id=skill_id,
                                                     trinket_id=trinket_id,
                                                     consumable_id=consumable_id,
                                                     class_name=self.selected_class_name,
                                                     talent_name=self.selected_talent_name,
                                                     game_version='retail')
                    if status == 1:
                        print(f"Icon downloaded successfully.")
                        self.reload_icons()
                    else:
                        error_message = {
                            -1: "Failed to download icon: HTTP or connection issue.",
                            -2: f"Failed to save the icon for '{skill_id}'.",
                            -3: f"Icon link not found for '{skill_id}'.",
                        }.get(status, "An unknown error occurred.")
                        print(f"Error: {error_message}")
                except Exception as e:
                    print(f"Error: An unexpected error occurred: {str(e)}")
            else:
                print("Warning: Please enter a valid skill ID.")
            print("Dialog was canceled.")  # Debug: Dialog canceled

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
        add_icon_button.setFixedWidth(120)
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
        button.setFixedWidth(120)
        button.setToolTip(ability_name)

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

    def retranslateUi(self, page_class):
        page_class.setWindowTitle(QCoreApplication.translate("ClassPage", "Class Page", None))

