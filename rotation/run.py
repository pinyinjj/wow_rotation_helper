import keyboard
import os
import time
import yaml
from .icon_loader import SkillIconLoader
from .matcher import ImageMatcher
from .user_key_binding import UserKeyBindLoader


class RotationHelper:
    def __init__(self, class_name, talent_name, config_file='rotation_config.yaml', keybind_file='config.json', game_version='retail'):
        self.game_version = game_version
        self.config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_file)
        self.rotation_config = self._load_rotation_config(self.config_file_path)

        self.user_key_bind_loader = UserKeyBindLoader(keybind_file)
        self.binded_abilities = self.user_key_bind_loader.binded_abilities()
        self.key_mapping = self.user_key_bind_loader.get_skill_key_mapping()
        self.threshold_mapping = self.user_key_bind_loader.get_skill_threshold_mapping()

        self.icon_loader = SkillIconLoader(class_name, talent_name, self.binded_abilities, game_version=self.game_version)
        self.images = self.icon_loader.get_images()

        self.matcher = ImageMatcher(self.images, self.key_mapping, self.rotation_config, self.game_version, self.threshold_mapping)

        # 循环与模式控制：
        # - is_running 为 False 时主循环结束
        # - mode: "preview" 只做匹配与预览，不按键；"run" 在热键按下时会按键
        self.is_running = True
        self.mode = "run"
        self.match_callback = None  # Callback function for when icon is matched

    def _load_rotation_config(self, config_file):
        default_set = {
            'delay': {'min': 0.069, 'max': 0.160},
            'screenshot_delay': 0.3,
            'region': {'x': 0, 'y': 0, 'width': 80, 'height': 200},
            'pressed_start': '`'
        }
        try:
            with open(config_file, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                # print(f"从 {config_file} 加载配置。")
                return config
        except FileNotFoundError:
            print(f"未找到配置文件 {config_file}，使用默认设置。")
            return default_set
        except yaml.YAMLError as e:
            print(f"读取 {config_file} 时出错: {e}")
            return default_set

    def set_mode(self, mode: str):
        """
        设置当前运行模式:
        - "preview": 只做截图 + 匹配 + 预览，不按键
        - "run":     截图 + 匹配，在热键按下时按键
        """
        if mode not in ("preview", "run"):
            return
        self.mode = mode

    def run(self):

        while self.is_running:
            # 控制整体循环节奏，避免占用过高 CPU
            time.sleep(0.1)
            try:
                # 根据模式与热键决定是否允许按键
                if self.mode == "run" and keyboard.is_pressed(self.rotation_config['pressed_start']):
                    # 运行模式 + 热键按下：允许 ImageMatcher 执行按键逻辑
                    self.matcher.enable_keys = True
                else:
                    # 预览模式或未按热键：禁用按键，仅用于匹配/预览
                    self.matcher.enable_keys = False

                # 无论预览还是运行模式，都执行一次截图 + 匹配流程
                self.matcher.match_images()
            except Exception as e:
                print(f"Error during execution: {e}")
                break

    def set_match_callback(self, callback):
        """Set callback function to be called when an icon is matched."""
        self.match_callback = callback
        # Also set callback in matcher
        self.matcher.set_match_callback(callback)
    
    def stop(self):
        """Signal to stop the loop."""
        # print("RH: Stopping RotationHelper.")
        self.is_running = False
