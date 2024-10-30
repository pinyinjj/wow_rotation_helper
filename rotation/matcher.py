import cv2
import numpy as np
import os
import time
from PIL import ImageGrab
import pygetwindow as gw
from datetime import datetime

from .key_presser import KeyPresser


class ImageMatcher:
    def __init__(self, icon_templates, key_mapping, config):
        """
        初始化图像匹配器。

        参数：
        - icon_templates：图标模板字典。
        - key_mapping：按键映射字典。
        - config：配置参数。
        """
        self.icon_templates = icon_templates
        self.key_mapping = key_mapping
        self.key_presser = KeyPresser(config)
        self.screenshot_delay = config['screenshot_delay']

        region_config = config['region']
        self.last_match = None
        self.region = (
            region_config['x1'],
            region_config['y1'],
            region_config['x2'],
            region_config['y2']
        )
        self.running = True
        self.manual_pause = False  # 手动暂停标志
        self.cast_time_skills = {
            '20241030222919': 4,
        }

    def is_cast_time_skill(self, key):
        """
        判断技能是否有施法时间。

        参数：
        - key：技能名称。

        返回：
        - 布尔值，表示是否有施法时间。
        - 施法时间（秒）。
        """
        if key in self.cast_time_skills:
            return True, self.cast_time_skills[key]
        return False, 0

    def resize_template(self, template, target_size):
        """
        将模板图像调整到指定尺寸。

        参数：
        - template：模板图像。
        - target_size：目标尺寸。

        返回：
        - 调整后的模板图像。
        """
        h_template, w_template = template.shape[:2]
        h_target, w_target = target_size
        if h_template != h_target or w_template != w_target:
            resized_template = cv2.resize(template, (w_target, h_target))
            return resized_template
        return template

    def take_screenshot(self):
        """
        截取屏幕的指定区域，并将图像从 RGB 转换为 BGR。
        """
        active_window = gw.getActiveWindow()
        if active_window and "魔兽世界" in active_window.title:
            try:
                screenshot = ImageGrab.grab(bbox=self.region)
                screenshot_np = np.array(screenshot)  # 这是 RGB 格式的图像
                # 将图像从 RGB 转换为 BGR
                screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
                return screenshot_bgr  # 返回 BGR 格式的图像
            except Exception as e:
                print(f"Failed to take screenshot: {e}")
                return None
        else:
            time.sleep(1)
            print("窗口未激活，不截图")
            return None

    def find_best_match(self, screenshot):
        """
        在截图中查找最佳匹配的图标模板，并使用彩色图像进行匹配。

        参数：
        - screenshot：截取的屏幕图像（BGR 格式）。
        返回：
        - 最佳匹配的模板名称。
        - 匹配得分。
        """
        if screenshot is None:
            print("未提供截图。")
            return None, -1


        if len(screenshot.shape) == 3:
            h_screenshot, w_screenshot, _ = screenshot.shape
        elif len(screenshot.shape) == 2:
            h_screenshot, w_screenshot = screenshot.shape
        else:
            return None, -1

        best_match = None
        best_match_value = -1

        # 用于存储匹配结果的列表
        match_results = []

        for name, icon_template in self.icon_templates.items():
            # 保留彩色模板用于匹配和展示（已经是 BGR 格式）
            h_template, w_template = icon_template.shape[:2]
            scale = min(h_screenshot / h_template, w_screenshot / w_template)
            new_size = (int(w_template * scale), int(h_template * scale))
            resized_template_color = cv2.resize(icon_template, new_size)

            try:
                # 进行模板匹配（使用彩色图像）
                result = cv2.matchTemplate(screenshot, resized_template_color, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                # 设置匹配阈值
                threshold = 0.8  # 您可以根据需要调整阈值
                if max_val >= threshold:
                    # 存储匹配结果
                    match_results.append((name, max_val, max_loc, resized_template_color.shape, resized_template_color))

                if max_val > best_match_value:
                    best_match_value = max_val
                    best_match = name

                # 展示模板和截图的对比（使用彩色图像）
                # self.show_comparison(screenshot, resized_template_color, name, max_val, max_loc)
            except Exception as e:
                print(f"匹配 {name} 时出错: {e}")
                continue

        # 可视化最佳匹配结果
        # if best_match is not None:
        #     # print(f"最佳匹配: {best_match}, 匹配得分: {best_match_value}")
        # else:
        #     print("没有找到合适的匹配。")

        return best_match, best_match_value

    def show_comparison(self, screenshot_color, template_color, template_name, match_value, top_left):
        """
        显示模板和截图的对比，以及它们之间的差异（彩色）。

        参数：
        - screenshot_color：截取的屏幕彩色图像（BGR 格式）。
        - template_color：模板彩色图像（BGR 格式）。
        - template_name：模板名称。
        - match_value：匹配得分。
        - top_left：匹配位置的左上角坐标。
        """
        h, w = template_color.shape[:2]

        # 在截图上绘制匹配区域
        screenshot_copy = screenshot_color.copy()
        cv2.rectangle(screenshot_copy, top_left, (top_left[0] + w, top_left[1] + h), (0, 255, 0), 2)
        cv2.putText(screenshot_copy, f"{template_name}: {match_value:.2f}", (top_left[0], top_left[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # 裁剪出匹配区域的图像
        matched_region = screenshot_color[top_left[1]:top_left[1] + h, top_left[0]:top_left[0] + w]

        # 检查裁剪是否超出图像边界
        if matched_region.shape[0] != h or matched_region.shape[1] != w:
            print("匹配区域大小与模板不一致，跳过显示。")
            return

        # 计算模板和匹配区域的差异（在彩色空间进行）
        diff = cv2.absdiff(template_color, matched_region)
        # 放大差异以增强可视化效果
        diff = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)

        # 将模板、匹配区域和差异拼接在一起
        comparison = np.hstack((template_color, matched_region, diff))

        # 调整窗口大小以适应图像
        cv2.namedWindow('模板 vs 匹配区域 vs 差异', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('模板 vs 匹配区域 vs 差异', 900, 300)
        cv2.imshow('模板 vs 匹配区域 vs 差异', comparison)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def handler_result(self, best_match):
        """
        根据最佳匹配结果执行相应操作。

        参数：
        - best_match：最佳匹配的技能名称。
        """
        active_window = gw.getActiveWindow()
        if active_window and "魔兽世界" in active_window.title:
            if best_match is not None:
                best_match = str(best_match[0])
                if isinstance(best_match, str):
                    if best_match in self.key_mapping:
                        self.process_skill_action(best_match)
                    else:
                        print(f"按键映射中未找到键 '{best_match}'。")
                else:
                    print("最佳匹配不是字符串，跳过输入。")
            else:
                print("未找到匹配项")
        else:
            print("魔兽世界窗口未聚焦，跳过输入。")

    def process_skill_action(self, best_match):
        """
        处理技能动作。

        参数：
        - best_match：最佳匹配的技能名称。
        """
        shortcut = self.get_skill_info(best_match)
        needs_cast_time, cast_time = self.is_cast_time_skill(best_match)

        if self.last_match != best_match:
            self.log_skill_usage(best_match, shortcut)
            self.last_match = best_match

        if needs_cast_time:
            self.execute_skill_with_cast(shortcut, cast_time, best_match)
        else:
            self.key_presser.press_key(shortcut)

    def get_skill_info(self, icon_name):
        """
        获取技能的快捷键信息。

        参数：
        - icon_name：技能图标名称。

        返回：
        - 技能对应的快捷键。
        """
        shortcut = self.key_mapping.get(icon_name, '未知按键')
        return shortcut

    def execute_skill_with_cast(self, shortcut, cast_time, icon_name):
        """
        执行有施法时间的技能。

        参数：
        - shortcut：技能快捷键。
        - cast_time：施法时间。
        - icon_name：技能图标名称。
        """
        start_time = time.time()
        end_time = start_time + cast_time

        while time.time() < end_time:
            remaining_time = end_time - time.time()
            if remaining_time + 1 > 1.0:
                self.key_presser.press_key(shortcut)
            time.sleep(0.1)

    def log_skill_usage(self, icon_name, shortcut):
        """
        记录技能使用日志。

        参数：
        - icon_name：技能图标名称。
        - shortcut：技能快捷键。
        """
        print(f"{time.strftime('%H:%M:%S')} 按下“{shortcut}” 使用“{icon_name}”")

    def match_images(self):
        """
        主图像匹配流程。
        """
        screenshot = self.take_screenshot()
        try:
            best_match = self.find_best_match(screenshot)
            self.handler_result(best_match)
        except Exception as e:
            print(f"匹配过程中出错: {e}")

