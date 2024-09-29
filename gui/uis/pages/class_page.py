import os
from PySide6.QtGui import QIcon, Qt
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QPushButton, QGridLayout, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QWidget, \
    QMainWindow, QSizePolicy, QFrame, QSplitter, QTextEdit, QGroupBox
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QTimer
from rotation import RotationThread
from gui.core.functions import Functions
from gui.widgets.py_line_edit import PyLineEdit
from gui.widgets.py_groupbox import PyGroupbox
from gui.core.json_themes import Themes
from gui.widgets.py_icon_button import PyIconButton
import json
import time


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

        # 创建 Base Ability Group
        self.base_ability = PyGroupbox("Class Base Abilities", self.themes)
        self.base_ability_layout = QGridLayout()
        self.base_ability.setLayout(self.base_ability_layout)
        self.page_skills_layout.addWidget(self.base_ability)
        self.base_ability.setVisible(False)

        # 创建 Talent Ability Group
        self.talent_ability = PyGroupbox("Talent Abilities", self.themes)
        self.talent_ability_layout = QGridLayout()
        self.talent_ability.setLayout(self.talent_ability_layout)
        self.page_skills_layout.addWidget(self.talent_ability)
        self.talent_ability.setVisible(False)

        self.button_layout = QHBoxLayout()
        self.page_skills_layout.addLayout(self.button_layout)

        self.load_button = self.create_button("icon_settings.svg")
        self.load_button.setText("加载")
        self.load_button.clicked.connect(self.save_config_with_rules)
        self.button_layout.addWidget(self.load_button)

        self.start_button = self.create_button("start.svg")
        self.start_button.setText("开始")
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

    def save_config_with_rules(self):
        """点击加载时，根据规则保存配置文件"""
        class_name = self.selected_class_name if self.selected_class else "unknown_class"
        talent_name = self.selected_talent_name if self.selected_talent else "unknown_talent"
        timestamp = time.strftime("%Y%m%d")

        config_filename = f"{class_name}_{talent_name}_{timestamp}.json"
        config_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "config")
        config_filepath = os.path.join(config_folder, config_filename)

        # 将配置保存到特定规则文件
        self.save_config_to_file(config_filepath)
        print(f"根据规则保存配置到 {config_filename}")

    def toggle_start_pause(self):
        if not self.is_running:
            print("Starting RotationThread...")
            self.start_button.setText("暂停")
            self.start_button.setIcon(QIcon(Functions.set_svg_icon("pause.svg")))
            self.is_running = True

            # 如果线程不存在，则创建并启动
            if not self.rotation_thread:
                print("Creating and starting new RotationThread.")
                self.rotation_thread = RotationThread(
                    config_file='rotation_config.yaml',
                    keybind_file='config.json',
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

    def create_separator(self, orientation="horizontal"):
        separator = QFrame()
        if orientation == "horizontal":
            separator.setFrameShape(QFrame.HLine)  # 水平线
            separator.setFrameShadow(QFrame.Sunken)  # 凹陷效果
        else:
            separator.setFrameShape(QFrame.VLine)  # 垂直线
            separator.setFrameShadow(QFrame.Sunken)  # 凹陷效果
        return separator

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

    def create_py_line_edit(self, ability_name):
        py_line_edit = PyLineEdit(
            text="",
            place_holder_text="输入快捷键",
            radius=8,
            border_size=2,
            color=self.themes["app_color"]["text_foreground"],
            selection_color=self.themes["app_color"]["white"],
            bg_color=self.themes["app_color"]["dark_one"],
            bg_color_active=self.themes["app_color"]["dark_three"],
            context_color=self.themes["app_color"]["context_color"]
        )

        # 当快捷键编辑完成时，自动保存到 config.json
        py_line_edit.editingFinished.connect(lambda: self.save_single_ability_config(ability_name, py_line_edit.text()))

        return py_line_edit

    def save_single_ability_config(self, ability_name, shortcut):
        """当任意技能的快捷键设置完成时，保存到 config.json"""
        if ability_name and shortcut:
            self.config_data[ability_name] = shortcut
            self.save_config_to_file(self.config_path)
            print(f"快捷键 '{shortcut}' 为技能 '{ability_name}' 已保存到 {self.config_path}")

    def save_config_to_file(self, file_path):
        """保存配置到指定路径的文件"""
        config_folder = os.path.dirname(file_path)
        if not os.path.exists(config_folder):
            os.makedirs(config_folder)

        with open(file_path, 'w') as config_file:
            json.dump(self.config_data, config_file, indent=4, ensure_ascii=False)
        print(f"配置已保存到 {config_file}")

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
            self.clear_layout(self.base_ability_layout)
            self.clear_layout(self.talent_ability_layout)
            self.talent_group.setVisible(False)
            self.base_ability.setVisible(False)
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

        self.clear_layout(self.base_ability_layout)
        self.clear_layout(self.talent_ability_layout)


        self.selected_talent_name = button.property("name")

        self.base_ability.setVisible(False)
        self.talent_ability.setVisible(False)

        self.load_class_base_icons(class_name)
        self.load_ability_icons(class_name, talent_name)

        # 显示基础技能和天赋技能组
        self.base_ability.setVisible(True)
        self.talent_ability.setVisible(True)
        self.relayout_for_ability_display()

    def clear_layout(self, layout):
        # 清理布局中的所有小部件
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

    def load_class_base_icons(self, class_name):
        base_dir = os.path.join(gui_dir, "uis", "icons", "talent_icons", class_name, "base")
        self.load_abilities(self.base_ability_layout, base_dir)
        self.base_ability.setVisible(True)
        self.adjust_main_window_size()

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
        base_ability_rows = (self.base_ability_layout.count() + 5) // 6
        talent_ability_rows = (self.talent_ability_layout.count() + 5) // 6

        icon_size = 48
        row_spacing = 10

        total_height = (
                (class_icon_rows + base_ability_rows + talent_icon_rows + talent_ability_rows)
                * (icon_size + row_spacing)
                + 200  # 额外缓冲空间
        )

        total_width_class = self.class_layout.count() * (icon_size + row_spacing) // 6
        total_width_talent = self.talent_layout.count() * (icon_size + row_spacing) // 4
        total_width_base = self.base_ability_layout.count() * (icon_size + row_spacing) // 6
        total_width_talent_ability = self.talent_ability_layout.count() * (icon_size + row_spacing) // 6

        total_width = max(total_width_class, total_width_talent, total_width_base, total_width_talent_ability)

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
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)

        abilities = self.load_abilities_from_directory(directory)

        row = 0
        col = 0

        for i, icon_path in enumerate(abilities):

            icon_label = QLabel()
            icon_label.setFixedSize(32, 32)
            icon_label.setScaledContents(True)

            if os.path.exists(icon_path):
                icon_label.setPixmap(QIcon(icon_path).pixmap(32, 32))

            ability_name = os.path.splitext(os.path.basename(icon_path))[0]

            ability_name_label = QLabel(ability_name)
            ability_name_label.setObjectName(f"ability_name_label_{i}")
            ability_name_label.setAlignment(Qt.AlignCenter)
            ability_name_label.setFixedWidth(32)
            ability_name_label.setWordWrap(True)
            ability_name_label.setStyleSheet("color: white;")

            icon_layout = QVBoxLayout()
            icon_layout.addWidget(icon_label)
            icon_layout.addWidget(ability_name_label)

            icon_widget = QWidget()
            icon_widget.setLayout(icon_layout)
            icon_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            py_line_edit = self.create_py_line_edit(ability_name)
            py_line_edit.setObjectName(f"line_edit_{i}")  # 设置唯一对象名称
            py_line_edit.setFixedHeight(40)
            py_line_edit.setFixedWidth(40)
            py_line_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            ability_layout = QHBoxLayout()
            ability_layout.setAlignment(Qt.AlignLeft)
            ability_layout.setSpacing(5)

            ability_layout.addWidget(icon_widget)
            ability_layout.addWidget(py_line_edit)

            ability_widget = QWidget()
            ability_widget.setLayout(ability_layout)

            layout.addWidget(ability_widget, row, col)

            col += 1
            if col == columns:
                col = 0
                row += 1

    def retranslateUi(self, page_class):
        page_class.setWindowTitle(QCoreApplication.translate("ClassPage", "Class Page", None))
