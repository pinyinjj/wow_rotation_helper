import os
import yaml
import json


class HekiliConfigFinder:
    def __init__(self, config_file='rotation_config.yaml', addon_name="Hekili"):
        """
        初始化 Hekili 配置查找器。

        :param config_file: 配置文件路径
        :param addon_name: 插件名称，默认为 "Hekili"
        """
        self.config = self.load_config(config_file)
        self.wow_directory = self.config.get('wow_directory', '')
        self.addon_name = addon_name
        self.saved_variables_path = self.get_saved_variables_path()

    def load_config(self, config_file):
        """
        从配置文件中加载设置。

        :param config_file: 配置文件路径
        :return: 配置字典
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                print(f"[INFO] Loaded configuration from {config_file}.")
                return config
        except FileNotFoundError:
            print(f"[ERROR] Configuration file {config_file} not found.")
            return {}
        except yaml.YAMLError as e:
            print(f"[ERROR] Error reading {config_file}: {e}")
            return {}

    def get_saved_variables_path(self):
        """
        获取插件的 SavedVariables 文件夹路径。

        :return: SavedVariables 文件夹路径
        """
        return os.path.join(self.wow_directory, "WTF", "Account", self.get_account_name(), "SavedVariables")

    def get_account_name(self):
        """
        获取魔兽世界账户名称。

        :return: 账户名称字符串
        """
        account_dir = os.path.join(self.wow_directory, "WTF", "Account")
        try:
            # 假设 WTF/Account 下只有一个文件夹，即账户名称
            account_name = next(os.walk(account_dir))[1][0]
            return account_name
        except IndexError:
            raise FileNotFoundError("No account directory found in WTF/Account.")

    def find_hekili_config(self):
        """
        查找 Hekili 配置文件（Hekili.lua）。

        :return: Hekili 配置文件的路径，如果未找到则返回 None
        """
        config_file = f"{self.addon_name}.lua"
        config_path = os.path.join(self.saved_variables_path, config_file)

        if os.path.exists(config_path):
            print(f"[INFO] Found Hekili configuration file: {config_path}")
            return config_path
        else:
            print("[WARNING] Hekili configuration file not found.")
            return None

    def load_hekili_config(self):
        """
        加载 Hekili 配置文件内容。

        :return: Hekili 配置文件的 JSON 数据，如果未找到则返回 None
        """
        config_path = self.find_hekili_config()
        if config_path:
            try:
                with open(config_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    # 使用 json.loads 假设内容是 JSON 格式
                    config_data = json.loads(content)
                    return config_data
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"[ERROR] Error loading Hekili configuration: {e}")
                return None
        else:
            return None

    def display_hekili_config(self):
        """
        显示加载的 Hekili 配置信息。
        """
        config_data = self.load_hekili_config()
        if config_data:
            print(json.dumps(config_data, indent=4))
        else:
            print("[INFO] No Hekili configuration to display.")


def main():
    hekili_finder = HekiliConfigFinder(config_file='rotation_config.yaml')
    hekili_finder.display_hekili_config()


if __name__ == "__main__":
    main()
