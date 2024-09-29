import cv2
import os
import numpy as np
from PIL import ImageGrab
import time
import yaml
import pygetwindow as gw
import keyboard
import threading
from .pixel_checker import ScreenColorChecker
from datetime import datetime



class ImageMatcher:
    def __init__(self, icon_templates, key_mapping, config):
        self.icon_templates = icon_templates
        self.key_mapping = key_mapping
        self.key_presser = KeyPresser(config)
        self.screenshot_delay = config['screenshot_delay']
        self.shortcut_config = config['shortcuts']
        region_config = config['region']
        pixel_check = config['pixel']
        self.last_match = None
        self.region = (
            region_config['x1'],
            region_config['y1'],
            region_config['x2'],
            region_config['y2']
        )
        self.running = True
        self.manual_pause = False  # 手动暂停标志
        self.color_checker = ScreenColorChecker(pixel_check)

        self.cast_time_skills = {
            'ConvoketheSpirits': 4,
        }

    def is_cast_time_skill(self, key):
        if key in self.cast_time_skills:
            return True, self.cast_time_skills[key]
        return False, 0

    def pause(self, manual=False):
        if self.running:
            print("Paused. Press F7 to resume.")
            self.running = False
            self.manual_pause = manual  # 标记是否为手动暂停

    def resume(self, manual=False):
        if not self.running:
            print("Resuming...")
            self.running = True
            self.manual_pause = not manual  # 解除手动暂停标志

    def resize_template(self, template, target_size):

        h_template, w_template = template.shape
        h_target, w_target = target_size
        if h_template > h_target or w_template > w_target:
            scaling_factor = min(h_target / h_template, w_target / w_template)
            new_size = (int(w_template * scaling_factor), int(h_template * scaling_factor))
            resized_template = cv2.resize(template, new_size)
            return resized_template
        return template

    def take_screenshot(self):
        """
        截取屏幕的指定区域。
        """
        active_window = gw.getActiveWindow()
        if active_window and "魔兽世界" in active_window.title:
            try:
                screenshot = ImageGrab.grab(bbox=self.region)
                return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
            except Exception as e:
                print(f"Failed to take screenshot: {e}")
                return None
        else:
            time.sleep(0.3)
            print("窗口未激活，不截图")

    def find_best_match(self, screenshot):
        """
        在截图中查找最佳匹配的图标模板。
        """
        best_match = None
        best_match_value = -1

        h_screenshot, w_screenshot = screenshot.shape
        for name, icon_template in self.icon_templates.items():
            resized_template = self.resize_template(icon_template, (h_screenshot, w_screenshot))
            h_template, w_template = resized_template.shape

            try:
                result = cv2.matchTemplate(screenshot, resized_template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                if max_val > best_match_value:
                    best_match_value = max_val
                    best_match = name  # 确保best_match是字符串，而不是数组
            except Exception as e:
                print(f"Error matching {name}: {e}")
                continue

        return best_match, best_match_value

    def handler_result(self, best_match):
        active_window = gw.getActiveWindow()
        if active_window and "魔兽世界" in active_window.title:
            if best_match is not None:
                if isinstance(best_match, str):  # 确保best_match是字符串

                    if best_match in self.key_mapping:
                        self.process_skill_action(best_match)  # 直接传递key
                    else:
                        print(f"Key '{best_match}' not found in key mapping.")
                else:
                    print("Best match is not a string. Skipping input.")
            else:
                print("No match found")
        else:
            print("WoW window not in focus; skipping input.")

    def process_skill_action(self, best_match):

        shortcut = self.get_skill_info(best_match)

        needs_cast_time, cast_time = self.is_cast_time_skill(best_match)

        if self.last_match != best_match:
            self.log_skill_usage(best_match, shortcut)
            self.last_match = best_match  # 更新上次匹配结果

        # 执行技能，并根据施法时间进行操作
        if needs_cast_time:
            print("执行读条")
            self.execute_skill_with_cast(shortcut, cast_time, best_match)
        else:
            self.key_presser.press_key(shortcut)

    def get_skill_info(self, icon_name):

        shortcut = self.key_mapping.get(icon_name, '未知按键')
        return shortcut

    def execute_skill_with_cast(self, shortcut, cast_time, icon_name):

        start_time = time.time()
        end_time = start_time + cast_time

        while time.time() < end_time:
            remaining_time = end_time - time.time()
            if remaining_time+1 > 1.0:
                self.key_presser.press_key(shortcut)  # 重复按下快捷键，直到施法结束
            time.sleep(0.1)  # 控制按键频率


    def log_skill_usage(self, icon_name, shortcut):
        """
        打印技能使用的日志。
        """
        print(
            f"{time.strftime('%H:%M:%S')} 按下“{shortcut}” 使用“{icon_name}”"
        )



    def wait_for_color_change(self, target_color, max_wait_time=5):
        """
        等待直到检测到指定颜色变化或超时。
        :param target_color: 目标颜色 ('purple', 'red', 'white')
        :param max_wait_time: 最大等待时间（秒）
        """
        start_time = time.time()
        # print(f"等待颜色变化为 {target_color}...")

        while time.time() - start_time < max_wait_time:
            color_result = self.color_checker.check_colors()
            # print(f"当前颜色检测结果: {color_result}")  # 添加调试打印来查看检测结果
            if color_result == target_color:
                # print('暂停')
                self.pause()
                break
            time.sleep(0.05)  # 增加检测频率
        else:
            print(f"未检测到颜色变化为 {target_color}，超时退出。")





    def match_images(self):
        print("Starting image matching...")

        while True:
            # 检查手动暂停状态，若为手动暂停，则跳过颜色检查
            if self.manual_pause:
                print("Manually paused, waiting...")
                time.sleep(0.5)
                continue

            # 仅当非手动暂停时，检查颜色状态
            color_result = self.color_checker.check_colors()
            if color_result == 'red' and not self.manual_pause:
                self.pause()
            elif color_result == 'white' and not self.manual_pause:
                self.resume()
            elif color_result == 'fixed' and not self.manual_pause:
                self.pause()
            else:
                self.running = False
                self.pause()

            # 运行匹配逻辑
            if not self.running:
                print("Paused, waiting...")
                time.sleep(0.5)
                continue

            screenshot = self.take_screenshot()
            if screenshot is None:
                continue

            best_match, best_match_value = self.find_best_match(screenshot)
            self.handler_result(best_match)

            time.sleep(self.screenshot_delay)


import pyautogui
import random


class KeyPresser:
    def __init__(self, config):
        """
        初始化按键类
        """
        self.min_delay = config['delay']['min']
        self.max_delay = config['delay']['max']
        self.set_random_delay()

    def set_random_delay(self):
        """
        设置按键之间的随机延迟。
        """
        self.delay = random.uniform(self.min_delay, self.max_delay)
        # print(f"Random delay set to: {self.delay:.3f} seconds")

    def press_key(self, key):
        """
        按下一个键。
        :param key: 要按下的键
        """
        try:
            key = str(key)  # 确保 key 是字符串类型
            # print(f"Pressing key: {key} with delay {self.delay:.3f} seconds")
            pyautogui.press(key)
            time.sleep(self.delay)
            self.set_random_delay()  # 每次按键后重新设置随机延迟
        except Exception as e:
            print(f"Error pressing key {key}: {e}")