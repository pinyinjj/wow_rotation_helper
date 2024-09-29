from .icon_loader import SkillIconLoader
import os
from .matcher import ImageMatcher
import yaml
import json
from .user_key_binding import UserKeyBindLoader
import time



class RotationHelper:
    def __init__(self, class_name, talent_name, config_file='rotation_config.yaml', keybind_file='config.json'):
        # 加载旋转配置
        self.config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_file)
        self.rotation_config = self._load_rotation_config(self.config_file_path)

        # 加载用户键位绑定
        self.user_key_bind_loader = UserKeyBindLoader(keybind_file)
        self.binded_abilities = self.user_key_bind_loader.binded_abilities()
        self.key_mapping = self.user_key_bind_loader.get_skill_key_mapping()

        # 加载图标
        self.icon_loader = SkillIconLoader(class_name, talent_name, self.binded_abilities)
        self.images = self.icon_loader.get_images()

        # 初始化 ImageMatcher
        self.matcher = ImageMatcher(self.images, self.key_mapping, self.rotation_config)

        # 控制线程状态的变量
        self.is_running = True
        self.is_paused = False

    def _load_rotation_config(self, config_file):
        """加载旋转配置文件，如果未找到配置文件则使用默认配置"""
        default_set = {
            'delay': {'min': 0.069, 'max': 0.160},
            'screenshot_delay': 0.3,
            'region': {'x': 0, 'y': 0, 'width': 80, 'height': 200},
            'shortcuts': {'pause': 'esc', 'continue': 'F7'}
        }
        try:
            with open(config_file, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                print(f"Configuration loaded from {config_file}.")
                return config
        except FileNotFoundError:
            print(f"Configuration file {config_file} not found. Using default settings.")
            return default_set
        except yaml.YAMLError as e:
            print(f"Error reading {config_file}: {e}")
            return default_set

    def run(self):
        """运行图像匹配的主逻辑"""
        while self.is_running:
            if self.is_paused:
                print("Rotation paused.")
                self._wait_until_resumed()  # 等待恢复
            else:
                self.matcher.match_images()  # 调用图像匹配的主逻辑

    def _wait_until_resumed(self):
        """等待恢复状态"""
        while self.is_paused and self.is_running:
            # 等待暂停解除
            time.sleep(0.5)  # 暂时延迟避免CPU过高使用

    def pause(self):
        """暂停旋转"""
        print("Pausing rotation...")
        self.is_paused = True
        self.matcher.pause()  # 调用 matcher 的暂停方法

    def resume(self):
        """恢复旋转"""
        print("Resuming rotation...")
        self.is_paused = False
        self.matcher.resume()  # 调用 matcher 的恢复方法

