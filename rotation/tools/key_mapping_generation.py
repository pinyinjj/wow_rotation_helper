import os
import yaml

def quoted_presenter(dumper, data):
    """
    自定义 YAML 表示器，用于强制为特定数据类型加上引号。
    """
    if isinstance(data, str):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')
    return dumper.represent_data(data)

# 为所有字符串类型添加自定义表示器
yaml.add_representer(str, quoted_presenter)

class KeyMappingManager:
    def __init__(self, base_directory):
        """
        初始化类，并设置基础目录。
        """
        self.base_directory = base_directory

    def load_existing_key_mapping(self, mapping_file):
        """
        从 key_mapping.yaml 文件中加载现有的映射。
        :param mapping_file: key_mapping.yaml 文件的路径
        :return: 图标映射字典
        """
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r', encoding='utf-8') as file:
                    icon_mapping = yaml.safe_load(file) or {}
                    print(f"  [INFO] Existing key_mapping.yaml loaded from {mapping_file}.")
                    return icon_mapping
            except yaml.YAMLError as e:
                print(f"  [ERROR] Error reading {mapping_file}: {e}")
        else:
            print(f"  [INFO] No key_mapping.yaml found. A new one will be created.")
        return {'icons': {}}

    def save_key_mapping(self, icon_mapping, mapping_file):
        """
        将图标映射保存到 key_mapping.yaml 文件中。
        :param icon_mapping: 图标映射字典
        :param mapping_file: key_mapping.yaml 文件的路径
        """
        with open(mapping_file, 'w', encoding='utf-8') as file:
            yaml.safe_dump(icon_mapping, file, allow_unicode=True, sort_keys=False)
            print(f"  [INFO] key_mapping.yaml has been updated/created in {os.path.dirname(mapping_file)}.")

    def add_missing_icons(self, talent_directory, existing_icons):
        """
        将缺失的图标条目添加到现有的映射中。
        :param talent_directory: 天赋文件夹路径
        :param existing_icons: 现有的图标映射字典
        :return: 是否有新条目被添加
        """
        new_entries_added = False
        for filename in os.listdir(talent_directory):
            if filename.lower().endswith('.tga'):
                key = os.path.splitext(filename)[0]
                if key not in existing_icons:
                    existing_icons[key] = {
                        'icon_name': '',
                        'shortcut': '',
                        'cast_time': 0,         # 新增参数，默认为0
                        'interruptable': True   # 新增参数，默认为True
                    }
                    print(f"    [ADD] New entry for {key} in key_mapping.yaml.")
                    new_entries_added = True
        return new_entries_added

    def ensure_parameters_exist(self, existing_icons):
        """
        确保每个图标条目都包含所有必要的参数。
        :param existing_icons: 现有的图标映射字典
        :return: 是否有条目被更新
        """
        updated = False
        for icon, attributes in existing_icons.items():
            if 'cast_time' not in attributes:
                attributes['cast_time'] = 0
                updated = True
            if 'interruptable' not in attributes:
                attributes['interruptable'] = True
                updated = True
        if updated:
            print("  [INFO] Missing parameters have been added to existing icons.")
        return updated

    def normalize_shortcuts(self, existing_icons):
        """
        将所有快捷键转换为小写。
        :param existing_icons: 现有的图标映射字典
        """
        for icon in existing_icons.values():
            if 'shortcut' in icon and isinstance(icon['shortcut'], str):
                icon['shortcut'] = icon['shortcut'].lower()

    def sort_icons(self, existing_icons):
        """
        根据快捷键顺序对图标进行排序。
        :param existing_icons: 现有的图标映射字典
        :return: 排序后的图标字典
        """
        def sort_key(item):
            shortcut = item[1].get('shortcut', '')
            order = {'1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '0': 10, '-': 11, '=': 12,
                     'q': 13, 'e': 14, 'r': 15, 't': 16, 'f': 17}
            return order.get(shortcut, 99)  # 未指定的快捷键排在最后

        return dict(sorted(existing_icons.items(), key=sort_key))

    def create_or_update_key_mapping(self, talent_directory):
        """
        检查 talent 文件夹中的 .tga 文件，并创建或更新 key_mapping.yaml 文件。
        """
        mapping_file = os.path.join(talent_directory, 'key_mapping.yaml')
        icon_mapping = self.load_existing_key_mapping(mapping_file)

        existing_icons = icon_mapping.get('icons', {})
        new_entries_added = self.add_missing_icons(talent_directory, existing_icons)

        self.normalize_shortcuts(existing_icons)

        # 检查并补充缺失的参数
        parameters_added = self.ensure_parameters_exist(existing_icons)

        if not new_entries_added and not parameters_added:
            print(f"  [INFO] No new icons or parameters to add in {talent_directory}.")
            return

        icon_mapping['icons'] = self.sort_icons(existing_icons)
        self.save_key_mapping(icon_mapping, mapping_file)

    def process_icon_directories(self):
        """
        遍历所有包含 .tga 文件的最深层目录，并生成或更新 key_mapping.yaml 文件。
        """
        processed_count = 0
        for root, dirs, files in os.walk(self.base_directory):
            relative_path = os.path.relpath(root, self.base_directory)
            print(f"[DIR] Processing directory: {relative_path}")

            if any(file.lower().endswith('.tga') for file in files):
                print(f"  [INFO] Found .tga files in {relative_path}.")
                self.create_or_update_key_mapping(root)
                processed_count += 1

        if processed_count == 0:
            print("[INFO] No directories containing .tga files were found.")
        else:
            print(f"\n[INFO] Processing complete. {processed_count} directories were processed.")

def main():
    base_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'skill_icons'))

    print(f"Starting processing of icon directories in: {base_directory}")

    manager = KeyMappingManager(base_directory)
    manager.process_icon_directories()

    print("Script finished executing.")

if __name__ == "__main__":
    main()
