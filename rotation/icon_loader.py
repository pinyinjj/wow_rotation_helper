from PIL import Image
import cv2
import os
import numpy as np

class SkillIconLoader:
    def __init__(self, class_name, talent_name, binded_abilities, game_version=''):
        """
        技能图标加载器，支持 Retail 和 Classic 版本。

        参数:
            class_name (str): 职业名称
            talent_name (str): 天赋名称
            binded_abilities (list): 绑定的技能名称列表
            game_version (str): 游戏版本，'retail' 或 'classic'
        """
        # 计算项目根目录，确保返回到项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 确定存储路径（Classic 版本需要额外的 'classic/' 文件夹）
        base_folder = "classic" if game_version.lower() == "classic" else ""

        self.base_directory = os.path.join(
            project_root, 'gui', 'uis', 'icons', base_folder, 'talent_icons', class_name
        )
        self.class_directory = os.path.join(self.base_directory, 'base')  # 通用基础目录
        self.talent_directory = os.path.join(self.base_directory, talent_name.lower())  # 天赋目录
        self.binded_abilities = binded_abilities  # 用户绑定的技能

        print(f"Game Version: {game_version}")
        print(f"Base Directory: {self.base_directory}")
        print(f"Base Icons Path: {self.class_directory}")
        print(f"Talent Icons Path: {self.talent_directory}")
        print(f"Bound Abilities: {self.binded_abilities}")

        self.images = self._load_images()

    def _load_images(self):
        """加载 'base' 和天赋技能文件夹中的图标"""
        images = {}

        # 加载 'base' 文件夹中的图标
        if os.path.exists(self.class_directory):
            images.update(self._load_images_from_directory(self.class_directory))
        else:
            print(f"[WARN] Base directory does not exist: {self.class_directory}")

        # 加载天赋文件夹中的图标
        if os.path.exists(self.talent_directory):
            images.update(self._load_images_from_directory(self.talent_directory))
        else:
            print(f"[WARN] Talent directory does not exist: {self.talent_directory}")

        print(f"[INFO] Loaded icons: {list(images.keys())}")
        return images

    def _load_images_from_directory(self, directory):
        """加载指定目录中的图标"""
        images = {}

        # 支持的文件扩展名
        supported_extensions = ('.tga', '.png', '.jpg', '.jpeg', '.bmp')

        for filename in os.listdir(directory):
            ability_name, ext = os.path.splitext(filename)

            # 检查文件是否在绑定的技能列表中，且扩展名受支持
            if ability_name in self.binded_abilities and ext.lower() in supported_extensions:
                image_path = os.path.join(directory, filename)
                try:
                    # 读取并转换图像
                    pil_image = Image.open(image_path).convert('RGB')
                    image = np.array(pil_image)
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # RGB 转 BGR

                    images[ability_name] = image
                except Exception as e:
                    print(f"[ERROR] Failed to load image: {filename}, error: {e}")
        return images

    def get_images(self):
        """返回已加载的图像"""
        return self.images
