import json
import os
import sys

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, Qt
from PySide6.QtWidgets import QPushButton, QGridLayout, QVBoxLayout, QLabel, QHBoxLayout, QWidget, \
    QMainWindow, QSizePolicy, QDialog, QTextEdit

from gui.core.functions import Functions
from gui.core.json_themes import Themes
from gui.widgets import PyGroupbox, PyPushButton, PyLoggerWindow
from rotation import RotationThread
from .key_binding import KeyBindDialog


current_dir = os.path.dirname(os.path.abspath(__file__))
gui_dir = os.path.join(current_dir, "..", "..")

class Ui_ClassPage(object):
    def __init__(self, main_window: QMainWindow):
        self.main_window = main_window
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
        # 创建 Class Group
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

        self.load_button = self.create_button("save.svg")
        self.load_button.setText("Save")
        self.load_button.clicked.connect(self.save_config_with_rules)
        self.button_layout.addWidget(self.load_button)

        self.start_button = self.create_button("start.svg")
        self.start_button.setText("Start")
        self.start_button.clicked.connect(self.toggle_start_pause)
        self.button_layout.addWidget(self.start_button)

        class_icon_path = os.path.join(gui_dir, "uis", "icons", "class_icons")
        class_icons = [f for f in os.listdir(class_icon_path) if f.endswith(".tga")]

        for i, icon_filename in enumerate(class_icons):
            class_name = os.path.splitext(icon_filename)[0]
            icon_path = os.path.join(class_icon_path, icon_filename)
            button = self.create_class_button(icon_path, QSize(64, 64), class_name,
                                              lambda _, class_name=class_name: self.load_talent_icons(class_name))
            self.class_layout.addWidget(button, i // 6, i % 6)

        self.adjust_class_icon_spacing()

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
        """加载配置文件夹中匹配职业和天赋的配置文件"""
        if not self.selected_class_name or not self.selected_talent_name:
            print("请先选择职业和天赋")
            return

        # 构建匹配文件名的前缀
        prefix = f"{self.selected_class_name}_{self.selected_talent_name}"

        # 获取所有匹配前缀的配置文件
        config_files = [f for f in os.listdir(self.config_folder) if f.startswith(prefix) and f.endswith('.json')]

        # 检查是否有匹配的配置文件
        if config_files:
            latest_filepath = os.path.join(self.config_folder, config_files[0])  # 加载第一个匹配的文件
            self.load_config_from_file(latest_filepath)
            print(f"加载配置文件：{config_files[0]}")
            return latest_filepath  # 返回加载的配置文件路径
        else:
            print("没有有效的配置文件")

    def load_config_from_file(self, filepath):
        """从配置文件中加载绑定并将输入框转换为按钮"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                config_data = json.load(file)
                self.config_data = config_data
                print(f"加载配置文件 {filepath} 成功: {config_data}")

                # 遍历配置并将按键绑定显示为按钮
                for ability_name, shortcut in config_data.items():
                    # print(f"尝试应用绑定：{ability_name} -> {shortcut}")
                    self.apply_binding_to_ui(ability_name, shortcut)  # 在此处应用绑定
        except FileNotFoundError:
            print(f"配置文件 {filepath} 未找到")
        except json.JSONDecodeError as e:
            print(f"解析配置文件错误: {e}")

    def apply_binding_to_ui(self, ability_name, shortcut):
        """根据已加载的按键绑定，将现有输入框转换为按钮"""
        # 遍历布局找到对应的 ability_name
        for i in range(self.talent_ability_layout.count()):
            widget = self.talent_ability_layout.itemAt(i).widget()
            if widget:
                # 检查 widget 中的 QLabel 是否有相应的 ability_name
                ability_layout = widget.layout()
                if isinstance(ability_layout.itemAt(0).widget(), QLabel):
                    label = ability_layout.itemAt(0).widget()
                    if ability_name == label.toolTip():  # 检查图标的 toolTip 是否匹配 ability_name
                        print(f"找到匹配的 ability: {ability_name}, 正在应用绑定...")
                        # 获取 PyLineEdit 和按钮
                        py_line_edit = ability_layout.itemAt(1).widget()
                        button = ability_layout.itemAt(2).widget()

                        # 设置按钮的文本为绑定的快捷键，并隐藏输入框
                        button.setText(shortcut.upper())
                        py_line_edit.setVisible(False)
                        button.setVisible(True)
                        return
        

    def toggle_start_pause(self):
        if not self.is_running:
            print("Starting RotationThread...")
            self.start_button.setText("停止")
            self.start_button.setIcon(QIcon(Functions.set_svg_icon("pause.svg")))
            self.is_running = True

            # 加载最新的配置文件
            config_filepath = self.load_latest_config()  # 获取最新的配置文件路径

            if not config_filepath:
                print("未找到配置文件，无法启动旋转线程")
                return

            # 如果线程不存在，则创建并启动
            if not self.rotation_thread:
                print("Creating and starting new RotationThread.")
                self.rotation_thread = RotationThread(
                    config_file='rotation_config.yaml',  # 旋转配置文件
                    keybind_file=config_filepath,  # 使用最新配置文件路径作为键绑定文件
                    class_name=self.selected_class_name,
                    talent_name=self.selected_talent_name
                )
                self.rotation_thread.finished.connect(self.on_thread_finished)

            self.rotation_thread.start()  # 启动线程
            print("RotationThread started.")
        else:
            if self.rotation_thread and self.is_running:
                if self.start_button.text() == "暂停":
                    print("Pausing RotationThread.")
                    self.start_button.setText("继续")
                    self.start_button.setIcon(QIcon(Functions.set_svg_icon("start.svg")))
                    self.rotation_thread.pause()  # 暂停线程
                else:
                    print("Resuming RotationThread.")
                    self.start_button.setText("暂停")
                    self.start_button.setIcon(QIcon(Functions.set_svg_icon("pause.svg")))
                    self.rotation_thread.resume()  # 恢复线程

    def on_thread_finished(self):
        # 当线程完成时处理任何清理工作
        self.rotation_thread = None
        self.is_running = False

    def create_button(self, icon="icon_heart.svg", size=40):
        button = QPushButton()
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

    def save_config_to_file(self, file_path):
        """保存当前所有绑定的技能和快捷键到文件，并打印写入流"""
        try:
            # 打印当前即将保存的配置内容
            print(f"准备写入的配置数据: {self.config_data}")

            # 打开文件并写入
            with open(file_path, 'w', encoding='utf-8') as config_file:
                json.dump(self.config_data, config_file, indent=4, ensure_ascii=False)

            # 打印成功消息和文件路径
            print(f"配置已成功写入到 {file_path}")

        except Exception as e:
            # 打印异常信息
            print(f"保存配置文件时出错: {e}")

    def adjust_class_icon_spacing(self, spacing_factor=1):
        window_width = self.main_window.width()
        columns = 6
        icon_size = 64
        total_padding = window_width - (columns * icon_size)
        spacing = total_padding // (columns + 1) * spacing_factor
        self.class_layout.setHorizontalSpacing(spacing)

    def create_class_button(self, icon_path, icon_size, class_name, on_click_callback):
        button = QPushButton()
        button.setProperty("name", class_name)
        icon = QIcon(icon_path)
        button.setIcon(icon)
        button.setIconSize(QSize(icon_size.width() - 10, icon_size.height() - 10))
        button.setFixedSize(icon_size.width(), icon_size.height())
        button.setStyleSheet(self.get_button_style(selected=False))
        button.clicked.connect(lambda _: self.on_class_button_clicked(button, on_click_callback))
        return button

    def on_class_button_clicked(self, button, on_click_callback):
        if self.selected_class and self.selected_class != button:
            self.selected_class.setStyleSheet(self.get_button_style(selected=False))
            self.clear_layout(self.talent_layout)
            self.clear_layout(self.talent_ability_layout)
            self.talent_group.setVisible(False)
            self.talent_ability.setVisible(False)

        self.selected_class = button
        self.selected_class_name = button.property("name")
        button.setStyleSheet(self.get_button_style(selected=True))
        on_click_callback(button)

        self.talent_group.setVisible(True)


    def relayout_for_talent_display(self):
        self.class_layout.setVerticalSpacing(10)
        self.adjust_class_icon_spacing()
        self.adjust_main_window_size()

    def on_talent_button_clicked(self, button, talent_name, class_name):
        if self.selected_talent and self.selected_talent != button:
            self.selected_talent.setStyleSheet(self.get_button_style(selected=False))

        self.selected_talent = button
        button.setStyleSheet(self.get_button_style(selected=True))

        self.clear_layout(self.talent_ability_layout)

        self.selected_talent_name = button.property("name")

        self.talent_ability.setVisible(False)

        # 在选择天赋后加载最新的配置文件
        self.load_latest_config()

        self.load_ability_icons(class_name, talent_name)

        self.talent_ability.setVisible(True)
        self.relayout_for_ability_display()

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
        button = QPushButton()
        print(f"create_talent_button {talent_name}")
        button.setProperty("name", talent_name)
        icon = QIcon(icon_path)
        button.setIcon(icon)
        button.setIconSize(QSize(icon_size.width() - 10, icon_size.height() - 10))
        button.setFixedSize(icon_size.width(), icon_size.height())
        button.setStyleSheet(self.get_button_style(selected=False))
        button.clicked.connect(lambda _: self.on_talent_button_clicked(button, talent_name, class_name))
        return button

    def load_talent_icons(self, class_name):
        for i in reversed(range(self.talent_layout.count())):
            self.talent_layout.itemAt(i).widget().setParent(None)

        talent_icon_path = os.path.join(gui_dir, "uis", "icons", "talent_icons", class_name)
        talent_icons = [f for f in os.listdir(talent_icon_path) if f.endswith(".tga")]

        for i, talent_icon in enumerate(talent_icons):
            icon_path = os.path.join(talent_icon_path, talent_icon)
            talent_name = os.path.splitext(talent_icon)[0].lower()
            button = self.create_talent_button(icon_path, QSize(64, 64), talent_name, class_name)
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
        talent_ability_rows = (self.talent_ability_layout.count() + 5) // 6

        icon_size = 48
        row_spacing = 10

        total_height = (
                (class_icon_rows + talent_icon_rows + talent_ability_rows)
                * (icon_size + row_spacing)
                + 200  # 额外缓冲空间
        )

        total_width_class = self.class_layout.count() * (icon_size + row_spacing) // 6
        total_width_talent = self.talent_layout.count() * (icon_size + row_spacing) // 4
        total_width_talent_ability = self.talent_ability_layout.count() * (icon_size + row_spacing) // 6

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

    def load_abilities(self, layout, directory, columns=8):
        """加载技能并创建按钮绑定"""
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)

        abilities = self.load_abilities_from_directory(directory)

        row = 0
        col = 0

        for i, icon_path in enumerate(abilities):

            icon_label = QLabel()
            icon_label.setFixedSize(32, 32)
            icon_label.setScaledContents(True)

            ability_name = os.path.splitext(os.path.basename(icon_path))[0]

            try:
                icon_label.setPixmap(QIcon(icon_path).pixmap(32, 32))
            except Exception as e:
                print(f"加载图标错误: {ability_name}, 错误: {e}")
                icon_label.setText("No Icon")

            icon_label.setToolTip(ability_name)

            icon_layout = QVBoxLayout()
            icon_layout.addWidget(icon_label)

            icon_widget = QWidget()
            icon_widget.setLayout(icon_layout)
            icon_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            # 创建绑定按钮
            button = self.create_binding_button(ability_name)

            # 如果配置文件中存在绑定，将其应用
            if ability_name in self.config_data:
                shortcut = self.config_data[ability_name]
                button.setText(shortcut.upper())  # 显示为大写

            button.setFixedHeight(40)
            button.setFixedWidth(100)  # 增加按钮的宽度

            ability_layout = QHBoxLayout()
            ability_layout.setAlignment(Qt.AlignLeft)
            ability_layout.setSpacing(5)

            ability_layout.addWidget(icon_widget)
            ability_layout.addWidget(button)  # 添加按钮

            ability_widget = QWidget()
            ability_widget.setLayout(ability_layout)

            layout.addWidget(ability_widget, row, col)

            col += 1
            if col == columns:
                col = 0
                row += 1

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

        button.setFixedHeight(40)
        button.setFixedWidth(40)
        button.setToolTip(ability_name)

        def on_button_clicked():
            """点击按钮后打开按键绑定对话框"""
            dialog = KeyBindDialog(self.main_window)
            if dialog.exec() == QDialog.Accepted:
                # 获取绑定的按键并设置按钮文本
                key_sequence = dialog.key_sequence
                if key_sequence:
                    button.setText(key_sequence.upper())
                    self.config_data[ability_name] = key_sequence.upper()  # 更新配置

        button.clicked.connect(on_button_clicked)

        return button

    def retranslateUi(self, page_class):
        page_class.setWindowTitle(QCoreApplication.translate("ClassPage", "Class Page", None))

