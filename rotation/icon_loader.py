from PIL import Image
import cv2
import os
import numpy as np

class SkillIconLoader:
    def __init__(self, class_name, talent_name, binded_abilities):
        # 计算项目根目录，确保返回到项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 构建基础和天赋的路径
        self.base_directory = os.path.join(
            project_root, 'gui', 'uis', 'icons', 'talent_icons', class_name
        )
        self.class_directory = 'base'
        self.talent_directory = talent_name.lower()  # 使用小写的天赋名称
        self.binded_abilities = binded_abilities  # 用户绑定的技能

        print(
            f"Loading icons from: {self.base_directory} for abilities: {self.binded_abilities}"
        )
        self.images = self._load_images()

    def _load_images(self):
        images = {}

        # 加载 'base' 文件夹中的图标
        base_path = os.path.join(self.base_directory, self.class_directory)
        print(f"Base directory path: {base_path}")
        if os.path.exists(base_path):
            images.update(self._load_images_from_directory(base_path))
        else:
            print(f"Base directory does not exist: {base_path}")

        # 加载天赋文件夹中的图标
        talent_path = os.path.join(self.base_directory, self.talent_directory)
        print(f"Talent directory path: {talent_path}")
        if os.path.exists(talent_path):
            images.update(self._load_images_from_directory(talent_path))
        else:
            print(f"Talent directory does not exist: {talent_path}")

        print(f"Loaded icons: {list(images.keys())}")
        return images

    def _load_images_from_directory(self, directory):
        images = {}

        # 支持的文件扩展名
        supported_extensions = ['.tga', '.png', '.jpg', '.jpeg']

        for filename in os.listdir(directory):
            ability_name = os.path.splitext(filename)[0]  # 去掉文件扩展名

            # 检查文件是否在绑定的技能列表中，且扩展名受支持
            if ability_name in self.binded_abilities and any(
                filename.lower().endswith(ext) for ext in supported_extensions
            ):
                image_path = os.path.join(directory, filename)
                try:
                    # 打开图像并转换为 RGB 格式
                    pil_image = Image.open(image_path).convert('RGB')
                    image = np.array(pil_image)
                    # 将颜色空间从 RGB 转换为 BGR，适用于 OpenCV
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                    images[ability_name] = image
                except Exception as e:
                    print(f"Failed to load image: {filename}, error: {e}")
        return images

    def get_images(self):
        return self.images
