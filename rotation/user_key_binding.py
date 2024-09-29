import os
import json

class UserKeyBindLoader:
    def __init__(self, config_filename='config.json'):
        self.config_filename = config_filename
        self.config_data = None
        self.skill_key_mapping = None

        # 初始化时加载配置文件
        self._load_user_binding()

    def _load_user_binding(self):
        current_directory = os.path.dirname(os.path.abspath(__file__))
        config_directory = os.path.join(current_directory, '..', 'gui', 'config')
        config_file_path = os.path.join(config_directory, self.config_filename)
        config_file_path = os.path.abspath(config_file_path)

        if not os.path.exists(config_file_path):
            print(f"配置文件 '{self.config_filename}' 未找到.")
            return None

        try:
            with open(config_file_path, 'r', encoding='utf-8') as file:
                self.config_data = json.load(file)
            self.skill_key_mapping = {skill_name: shortcut for skill_name, shortcut in self.config_data.items()}
            print(f"成功加载配置文件: {self.config_filename}")
        except Exception as e:
            print(f"无法加载配置文件 '{self.config_filename}'，发生错误: {e}")
            self.skill_key_mapping = None

    def get_skill_key_mapping(self):
        return self.skill_key_mapping

    def binded_abilities(self):
        if self.skill_key_mapping:
            return list(self.skill_key_mapping.keys())
        return []


