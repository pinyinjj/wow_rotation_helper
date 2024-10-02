import keyboard
import os
import time
import yaml
from .icon_loader import SkillIconLoader
from .matcher import ImageMatcher
from .user_key_binding import UserKeyBindLoader


class RotationHelper:
    def __init__(self, class_name, talent_name, config_file='rotation_config.yaml', keybind_file='config.json'):
        """
        初始化旋转助手。

        参数：
        - class_name：职业名称。
        - talent_name：天赋名称。
        - config_file：配置文件名称。
        - keybind_file：键位绑定文件名称。
        """
        self.config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_file)
        self.rotation_config = self._load_rotation_config(self.config_file_path)

        self.user_key_bind_loader = UserKeyBindLoader(keybind_file)
        self.binded_abilities = self.user_key_bind_loader.binded_abilities()
        self.key_mapping = self.user_key_bind_loader.get_skill_key_mapping()

        self.icon_loader = SkillIconLoader(class_name, talent_name, self.binded_abilities)
        self.images = self.icon_loader.get_images()

        self.matcher = ImageMatcher(self.images, self.key_mapping, self.rotation_config)

    def _load_rotation_config(self, config_file):
        """
        加载旋转配置文件。

        参数：
        - config_file：配置文件路径。

        返回：
        - 配置字典。
        """
        default_set = {
            'delay': {'min': 0.069, 'max': 0.160},
            'screenshot_delay': 0.3,
            'region': {'x': 0, 'y': 0, 'width': 80, 'height': 200},
            'shortcuts': {'pause': 'esc', 'continue': 'F7'}
        }
        try:
            with open(config_file, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                print(f"从 {config_file} 加载配置。")
                return config
        except FileNotFoundError:
            print(f"未找到配置文件 {config_file}，使用默认设置。")
            return default_set
        except yaml.YAMLError as e:
            print(f"读取 {config_file} 时出错: {e}")
            return default_set

    def run(self):
        """
        运行图像匹配的主逻辑。
        """
        while True:
            try:
                if keyboard.is_pressed('1'):
                    self.matcher.match_images()
                time.sleep(0.1)
            except Exception as e:
                print(f"运行时遇到错误: {e}")
                break
