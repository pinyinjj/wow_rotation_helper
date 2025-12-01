import sys
import os
from datetime import datetime

import yaml
import cv2
import numpy as np
from PIL import ImageGrab
from PySide6.QtCore import Qt, QRect, QPoint, QSize, QTimer
from PySide6.QtGui import QPainter, QPen, QPixmap, QGuiApplication, QColor, QRegion, QIcon, QImage
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QMainWindow, QPushButton, QHBoxLayout, QFileDialog, \
    QGridLayout, QMessageBox

from gui.core.functions import Functions
from gui.core.json_themes import Themes
from rotation.template_matcher import TemplateMatcher

# 与 class_page 中保持一致的目录计算
current_dir = os.path.dirname(os.path.abspath(__file__))
gui_dir = os.path.join(current_dir, "..", "..")


class Ui_CapturePage(QMainWindow):
    def __init__(self, main_window: QMainWindow):
        super().__init__()
        self.main_window = main_window
        self.is_selecting = False
        self.x0 = self.y0 = self.x1 = self.y1 = 0
        self.selection_rect = QRect()
        self.screenshot = None  # Store the full screenshot

        # 预览相关缓存（按当前天赋缓存模板）
        self.preview_templates = None  # 用于存储当前天赋下的模板 (name, bgr) 列表
        self.preview_class_name = None
        self.preview_talent_name = None

        # 实时预览定时器（默认关闭）
        self.preview_timer = QTimer(self)
        self.preview_timer.setInterval(int(1000 / 60))  # 60 FPS
        self.preview_timer.timeout.connect(self._preview_tick)
        self.preview_active = False


    def setupUi(self, capture_page):
        # LOAD THEME COLOR
        # ///////////////////////////////////////////////////////////////
        themes = Themes()
        self.themes = themes.items

        # 手动框选截屏预览
        self.cropped_image_label = QLabel(self)
        self.cropped_image_label.setFixedSize(200, 200)
        self.cropped_image_label.setStyleSheet("border: 1px solid black;")

        # 使用 rotation_config.yaml 中区域的预览
        self.region_preview_label = QLabel(self)
        self.region_preview_label.setFixedSize(200, 200)
        self.region_preview_label.setStyleSheet("border: 1px solid black;")

        # 当前最匹配的图标预览
        self.best_icon_label = QLabel(self)
        self.best_icon_label.setFixedSize(64, 64)
        self.best_icon_label.setStyleSheet("border: 1px solid black;")

        self.coordinates_label = QLabel(self)
        self.coordinates_label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 150); padding: 5px;")
        self.coordinates_label.setVisible(False)

        # 按钮区
        self.start_button = self.create_button(icon="trim_icon.svg")
        self.start_button.setText("Capture")
        self.start_button.clicked.connect(self.start_capture)

        self.save_icon_button = self.create_button(icon="save_icon.svg")
        self.save_icon_button.setText("Save Icon")
        self.save_icon_button.clicked.connect(self.save_icon_as)

        self.get_info_button = self.create_button()
        self.get_info_button.setText("Save Location")
        self.get_info_button.clicked.connect(self.save_selection_info)

        self.preview_region_button = self.create_button(icon="refresh.svg")
        self.preview_region_button.setText("Preview Region")
        self.preview_region_button.clicked.connect(self.toggle_preview_region)

        self.capture_page_layout = QGridLayout(capture_page)

        self.info_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.start_button)
        self.button_layout.addWidget(self.save_icon_button)
        self.button_layout.addWidget(self.get_info_button)
        self.button_layout.addWidget(self.preview_region_button)

        # 网格布局：
        # [0,0] 手动截取预览  [0,1] 配置区域预览
        # [1,0] 最佳匹配图标  [1,1] 坐标文字
        self.capture_page_layout.addWidget(self.cropped_image_label, 0, 0)
        self.capture_page_layout.addWidget(self.region_preview_label, 0, 1)
        self.capture_page_layout.addWidget(self.best_icon_label, 1, 0)
        self.capture_page_layout.addWidget(self.coordinates_label, 1, 1)
        self.capture_page_layout.addLayout(self.button_layout, 2, 0, 1, 2)

        self.full_screen_label = QLabel()
        self.full_screen_label.setGeometry(QGuiApplication.primaryScreen().geometry())
        self.full_screen_label.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

    def save_selection_info(self):
        """Save the current selection coordinates to a YAML file."""
        if self.selection_rect.isNull():
            print("No selection made.")
            return

        new_region = {
            "x1": self.x0,
            "y1": self.y0,
            "x2": self.x1,
            "y2": self.y1
        }

        config = self.load_config()
        config['region'] = new_region
        self.save_config(config)

    def load_config(self):
        """Load the current configuration from the YAML file."""
        try:
            with open('rotation/rotation_config.yaml', 'r', encoding='utf-8') as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            return {}

    def save_config(self, config):
        """Save the configuration to the YAML file."""
        with open('rotation/rotation_config.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(config, file)

    # --------------------
    # 预览模板与匹配工具函数
    # --------------------
    def _load_preview_templates(self):
        """
        加载用于预览的模板图标。

        要求：
        - 必须已经在 Talents 页面选择完当前 talent，且技能图标已弹出；
        - 从当前 class + talent 对应的图标目录加载模板：
          gui/uis/icons/talent_icons/<class>/<talent>/
        """
        # 从主窗口拿到零售页面的 class_page 实例
        class_page = getattr(getattr(self.main_window.ui, "load_pages", None), "ui_class_page", None)
        if class_page is None:
            print("未找到 Ui_ClassPage，无法进行预览匹配。")
            return []

        # 必须先选择职业和天赋，且天赋技能已经显示出来
        if not class_page.selected_class_name or not class_page.selected_talent_name:
            print("请先在 Talents 页面选择职业和天赋，然后再使用预览。")
            return []
        if not class_page.talent_ability.isVisible():
            print("天赋技能列表尚未显示，请先选择天赋让技能图标弹出。")
            return []

        class_name = class_page.selected_class_name
        talent_name = class_page.selected_talent_name.lower()

        # 如果职业和天赋没有变化，则直接使用缓存
        if (
            self.preview_templates is not None
            and self.preview_class_name == class_name
            and self.preview_talent_name == talent_name
        ):
            return self.preview_templates

        # talent 对应的图标文件夹
        templates_dir = os.path.join(gui_dir, "uis", "icons", "talent_icons", class_name, talent_name)
        if not os.path.isdir(templates_dir):
            print(f"未找到天赋图标目录: {templates_dir}")
            return []

        loaded = []
        # 与 class_page.load_abilities_from_directory 支持的扩展名保持一致
        supported_extensions = (".tga", ".png", ".jpg", ".jpeg")
        for filename in os.listdir(templates_dir):
            if not filename.lower().endswith(supported_extensions):
                continue
            path = os.path.join(templates_dir, filename)
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img is None or img.size == 0:
                continue
            # 统一为 BGR
            if img.ndim == 3 and img.shape[2] == 4:
                tmpl_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            elif img.ndim == 3:
                tmpl_bgr = img
            else:
                tmpl_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

            # 使用文件名（不含扩展名）作为模板名，方便和技能名对应
            name = os.path.splitext(filename)[0]
            loaded.append((name, tmpl_bgr))

        if not loaded:
            print(f"天赋目录中未找到可用的图标: {templates_dir}")

        # 更新缓存标记
        self.preview_templates = loaded
        self.preview_class_name = class_name
        self.preview_talent_name = talent_name
        return self.preview_templates

    def _match_best_icon(self, frame_bgr, scale: float):
        """
        使用与运行时完全相同的匹配函数：
        - 在给定的 BGR 截图上执行**彩色模板匹配 + 缩放**，返回最佳模板名称及其图像。
        - 实际调用的是公共封装 `TemplateMatcher.match_best_icon_with_scale`。
        """
        templates = self._load_preview_templates()
        if not templates or frame_bgr is None or frame_bgr.size == 0:
            return None, None, None

        # 将 (name, tmpl_bgr) 列表转换为 {name: tmpl_bgr} 字典，供公共匹配函数使用
        templates_dict = {
            name: tmpl_bgr for name, tmpl_bgr in templates
            if tmpl_bgr is not None and getattr(tmpl_bgr, "size", 0) > 0
        }
        if not templates_dict:
            return None, None, None

        best_name, best_img_info, best_score = TemplateMatcher.match_best_icon_with_scale(
            frame_bgr, templates_dict, scale
        )
        return best_name, best_img_info, best_score

    def _numpy_to_qimage(self, bgr_image: np.ndarray) -> QImage:
        """将 BGR 的 numpy 图像转换为 QImage。"""
        if bgr_image is None or bgr_image.size == 0:
            return QImage()
        rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        return QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()

    def save_icon_as(self):
        """ Save the cropped screenshot to a user-selected directory. """
        if self.cropped_image_label.pixmap() is None:
            print("No image to save.")
            return

        # Generate a current timestamp string
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        # Open a dialog to select the save file path, with a default name based on the timestamp
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", f"{timestamp}.png", "PNG Files (*.png);;All Files (*)"
        )

        if file_path:
            # Save the pixmap from cropped_image_label as an image file
            self.cropped_image_label.pixmap().save(file_path, "PNG")
            print(f"Screenshot saved to: {file_path}")

    def create_button(self, icon="icon_heart.svg", size=40):
        button = QPushButton()
        icon_path = Functions.set_svg_icon(icon)
        button.setIcon(QIcon(icon_path))
        button.setFixedSize(size + 100, size)
        button.setIconSize(QSize(size - 10, size - 10))
        # 设置按钮的样式，使用主题颜色
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.themes["app_color"]["bg_two"]};
                border-radius: 8px;
                color: {self.themes["app_color"]["text_foreground"]};
                border: 2px solid {self.themes["app_color"]["bg_two"]};
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {self.themes["app_color"]["bg_three"]};
                color: {self.themes["app_color"]["icon_hover"]};
                border-color: {self.themes["app_color"]["bg_three"]};
            }}
            QPushButton:pressed {{
                background-color: {self.themes["app_color"]["bg_one"]};
                color: {self.themes["app_color"]["text_active"]};
                border-color: {self.themes["app_color"]["bg_one"]};
            }}
            QPushButton:checked {{
                background-color: {self.themes["app_color"]["context_color"]};
                color: {self.themes["app_color"]["white"]};
                border-color: {self.themes["app_color"]["context_color"]};
            }}
        """)
        return button

    # --------------------
    # 配置区域预览
    # --------------------
    def toggle_preview_region(self):
        """
        开关实时预览：
        - 开启时以 60FPS 连续刷新当前 region 的匹配结果；
        - 关闭时停止定时器，保留最后一帧画面。
        """
        if self.preview_active:
            # 停止预览
            self.preview_timer.stop()
            self.preview_active = False
            self.preview_region_button.setText("Preview Region")
            self.preview_region_button.setIcon(QIcon(Functions.set_svg_icon("refresh.svg")))
        else:
            # 启动预览前，先尝试加载一次模板，确保已经选择了职业和天赋
            self.preview_templates = None
            self.preview_class_name = None
            self.preview_talent_name = None

            templates = self._load_preview_templates()
            if not templates:
                # 未选择职业/天赋或天赋技能未弹出时，弹出提示窗口而不是在命令行刷提示
                QMessageBox.warning(
                    self,
                    "预览错误",
                    "请先在 Talents 页面选择职业和天赋，并确保技能图标已经显示，然后再使用预览。",
                )
                return

            self.preview_timer.start()
            self.preview_active = True
            self.preview_region_button.setText("Stop Preview")
            self.preview_region_button.setIcon(QIcon(Functions.set_svg_icon("pause.svg")))

    def _preview_tick(self):
        """定时器回调：每一帧执行一次预览刷新。"""
        self.preview_current_region()

    def preview_current_region(self):
        """
        根据 rotation_config.yaml 中的 region，截取当前屏幕区域，
        并在界面中预览该区域以及当前最匹配的一个模板图标。
        """
        config = self.load_config()
        region_cfg = config.get("region")
        if not region_cfg:
            print("rotation_config.yaml 中没有找到 region 配置。")
            return

        # 目前 rotation_config.yaml 使用 x1,y1,x2,y2 坐标
        try:
            x1 = int(region_cfg.get("x1"))
            y1 = int(region_cfg.get("y1"))
            x2 = int(region_cfg.get("x2"))
            y2 = int(region_cfg.get("y2"))
        except Exception as e:
            print(f"region 配置格式错误: {e}")
            return

        if x2 <= x1 or y2 <= y1:
            print("region 配置的坐标无效。")
            return

        try:
            bbox = (x1, y1, x2, y2)
            screenshot = ImageGrab.grab(bbox=bbox)
        except Exception as e:
            print(f"截取配置区域失败: {e}")
            return

        screenshot_np = np.array(screenshot)  # RGB（在 HDR 开启时通常会偏亮）
        frame_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

        # 针对 HDR 做一次亮度压缩，和 rotation 中的匹配逻辑保持一致
        frame_bgr = self._apply_hdr_correction(frame_bgr)

        # 使用与运行时相同的缩放倍率（zoom），默认为 1.0
        zoom = float(config.get("zoom", 1.0))

        # 匹配最佳模板（完全复用运行时的匹配函数）
        best_name, best_img_info, best_score = self._match_best_icon(frame_bgr, zoom)

        # 在配置区域预览中标出匹配框
        frame_for_show = frame_bgr.copy()
        if best_img_info is not None:
            tmpl_bgr, top_left, (w, h) = best_img_info
            x, y = top_left
            cv2.rectangle(frame_for_show, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # 显示配置区域截图
        qimg_region = self._numpy_to_qimage(frame_for_show)
        pixmap_region = QPixmap.fromImage(qimg_region)
        pixmap_region = pixmap_region.scaled(
            self.region_preview_label.width(),
            self.region_preview_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.region_preview_label.setPixmap(pixmap_region)

        # 显示最佳匹配图标
        if best_img_info is not None:
            tmpl_bgr, _, _ = best_img_info
            qimg_icon = self._numpy_to_qimage(tmpl_bgr)
            pixmap_icon = QPixmap.fromImage(qimg_icon)
            pixmap_icon = pixmap_icon.scaled(
                self.best_icon_label.width(),
                self.best_icon_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.best_icon_label.setPixmap(pixmap_icon)

        # 在坐标标签中展示匹配信息
        if best_name is not None and best_score is not None:
            self.coordinates_label.setText(
                f"Region: ({x1}, {y1}) - ({x2}, {y2}) | Best: {best_name} ({best_score:.2f})"
            )
            self.coordinates_label.adjustSize()
            self.coordinates_label.setVisible(True)

    def _apply_hdr_correction(self, frame_bgr):
        """
        针对开启 HDR 时截图偏亮的问题，对截图做一次「色调映射」而不是简单整体变暗。

        目标：在预览中尽可能还原游戏画面本来的色彩，而不是单纯降低亮度。

        实现方式与 `rotation/matcher.py` 中保持一致：
        - 在近似线性 RGB 空间下计算亮度 Y
        - 对亮度做 Reinhard 风格的压缩：Y' = Y / (1 + Y)
          * 中间灰附近几乎不变，只在高光区明显压缩，防止过曝
        - 使用比例因子 scale = Y' / (Y + eps) 缩放每个像素的 RGB
          * 基本维持 R:G:B 比例不变，从而尽量保持原始色彩关系
        - 失败时直接返回原图，避免影响正常使用
        """
        # 直接调用公共封装，确保与运行时一致
        return TemplateMatcher.apply_hdr_correction(frame_bgr)

    def start_capture(self):
        """ Capture the current screen and start the selection process. """
        # Grab the current screen's screenshot
        screen = QGuiApplication.primaryScreen()
        self.screenshot = screen.grabWindow(0).toImage()

        self.x0 = self.y0 = self.x1 = self.y1 = 0
        self.is_selecting = False
        self.selection_rect = QRect()

        # Display the screenshot in the full-screen label
        self.full_screen_label.setPixmap(QPixmap.fromImage(self.screenshot))
        self.full_screen_label.setVisible(True)
        self.full_screen_label.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.full_screen_label.setCursor(Qt.CrossCursor)
        self.showFullScreen()

    def mousePressEvent(self, event):
        """ Start the selection process when the left mouse button is pressed. """
        if event.button() == Qt.LeftButton:
            self.is_selecting = True
            self.x0, self.y0 = event.position().toPoint().x(), event.position().toPoint().y()

    def mouseMoveEvent(self, event):
        """ Update the selection rectangle as the mouse moves. """
        if self.is_selecting:
            self.x1, self.y1 = event.position().toPoint().x(), event.position().toPoint().y()
            self.selection_rect = QRect(QPoint(self.x0, self.y0), QPoint(self.x1, self.y1)).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        """ Finish the selection process when the left mouse button is released. """
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.x1, self.y1 = event.position().toPoint().x(), event.position().toPoint().y()
            scale_factor = QApplication.primaryScreen().devicePixelRatio()
            self.selection_rect = QRect(QPoint(self.x0, self.y0), QPoint(self.x1, self.y1)).normalized()

            # Adjust coordinates
            adjusted_x0, adjusted_y0 = int(self.x0 * scale_factor), int(self.y0 * scale_factor)
            adjusted_x1, adjusted_y1 = int(self.x1 * scale_factor), int(self.y1 * scale_factor)

            # Extract the selected area
            width = abs(adjusted_x1 - adjusted_x0)
            height = abs(adjusted_y1 - adjusted_y0)
            cropped_image = self.screenshot.copy(adjusted_x0, adjusted_y0, width, height)

            # Display the cropped image
            self.display_cropped_image(cropped_image)

            # Restore window settings
            self.setWindowFlags(Qt.Widget)
            self.setWindowState(Qt.WindowNoState)
            self.setCursor(Qt.ArrowCursor)
            # self.show()
            self.display_coordinates(self.x0, self.y0, self.x1, self.y1)

    def display_coordinates(self, x0, y0, x1, y1):
        """ Display the coordinates of the selection. """
        self.coordinates_label.setText(f"x0y0: ({x0}, {y0}), x1y1: ({x1}, {y1})")
        self.coordinates_label.adjustSize()
        self.coordinates_label.move(10, 10)
        self.coordinates_label.setVisible(True)

    def display_cropped_image(self, cropped_image):
        """ Display the cropped screenshot in the QLabel widget. """
        if cropped_image:
            pixmap = QPixmap.fromImage(cropped_image)
            image_width = pixmap.width()
            image_height = pixmap.height()

            # If the image exceeds 300x300, scale it proportionally
            if image_width > 300 or image_height > 300:
                pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            # Adjust the label size to the image size or keep it 200x200 minimum
            self.cropped_image_label.setFixedSize(
                max(200, pixmap.width()), max(200, pixmap.height())
            )

            self.cropped_image_label.setPixmap(pixmap)

    def paintEvent(self, event):
        """ Draw the selection rectangle and mask the rest of the screen. """
        if self.screenshot:
            painter = QPainter(self)
            painter.drawPixmap(0, 0, QPixmap.fromImage(self.screenshot))

            # Mask the rest of the screen
            full_region = QRegion(self.rect())
            if not self.selection_rect.isNull():
                selection_region = QRegion(self.selection_rect)
                masked_region = full_region.subtracted(selection_region)
            else:
                masked_region = full_region

            painter.setClipRegion(masked_region)
            painter.fillRect(self.rect(), QColor(0, 0, 0, 90))  # Transparent black

            # Draw the selection rectangle
            if not self.selection_rect.isNull():
                pen = QPen(Qt.red, 2, Qt.SolidLine)
                painter.setPen(pen)
                painter.drawRect(self.selection_rect)

