import os
import json

class UserKeyBindLoader:
    def __init__(self, config_filename='config.json'):
        self.config_filename = config_filename
        self.config_data = None
        self.skill_key_mapping = None
        self.skill_threshold_mapping = None  # 新增：技能阈值映射

        # 初始化时加载配置文件
        self._load_user_binding()

    def _load_user_binding(self):
        # 支持完整路径或相对路径
        if os.path.isabs(self.config_filename) or os.path.exists(self.config_filename):
            # 如果是绝对路径或当前目录下存在，直接使用
            config_file_path = os.path.abspath(self.config_filename)
        else:
            # 否则在默认配置目录下查找
            current_directory = os.path.dirname(os.path.abspath(__file__))
            config_directory = os.path.join(current_directory, '..', 'gui', 'config')
            config_file_path = os.path.join(config_directory, self.config_filename)
            config_file_path = os.path.abspath(config_file_path)

        if not os.path.exists(config_file_path):
            print(f"配置文件 '{config_file_path}' 未找到.")
            return None

        try:
            with open(config_file_path, 'r', encoding='utf-8') as file:
                self.config_data = json.load(file)
            
            # 支持新格式 [shortcut, threshold] 和旧格式 shortcut
            self.skill_key_mapping = {}
            self.skill_threshold_mapping = {}
            
            for skill_name, config_value in self.config_data.items():
                # 跳过特殊字段（如 zoom, hdr_darkness）
                if skill_name in ("zoom", "hdr_darkness", "Add a new icon"):
                    continue
                    
                # 如果是列表格式 [shortcut, threshold]
                if isinstance(config_value, list) and len(config_value) >= 1:
                    self.skill_key_mapping[skill_name] = config_value[0]
                    # 如果有阈值，保存阈值
                    if len(config_value) >= 2:
                        self.skill_threshold_mapping[skill_name] = float(config_value[1])
                # 如果是字符串格式（旧格式），只有快捷键
                elif isinstance(config_value, str):
                    self.skill_key_mapping[skill_name] = config_value
                    # 旧格式没有阈值，不添加到 threshold_mapping 中
            
            print(f"成功加载配置文件: {self.config_filename}")
        except Exception as e:
            print(f"无法加载配置文件 '{self.config_filename}'，发生错误: {e}")
            self.skill_key_mapping = None
            self.skill_threshold_mapping = None

    def get_skill_key_mapping(self):
        return self.skill_key_mapping
    
    def get_skill_threshold_mapping(self):
        """获取技能阈值映射字典"""
        return self.skill_threshold_mapping

    def binded_abilities(self):
        if self.skill_key_mapping:
            return list(self.skill_key_mapping.keys())
        return []


