import pyautogui
import numpy as np
from PIL import ImageGrab, Image

class ScreenColorChecker:
    def __init__(self, config):
        """
        初始化屏幕颜色检查器
        :param config: 包含两个点(x1, y1, x2, y2)的配置
        """
        self.x1 = config['x1']
        self.y1 = config['y1']
        self.x2 = config['x2']
        self.y2 = config['y2']

        # 生成四个角点的坐标
        self.points = [(self.x1, self.y1),  # 左上角
                       (self.x2, self.y1),  # 右上角
                       (self.x2, self.y2),  # 右下角
                       (self.x1, self.y2)]  # 左下角

        # 使用十六进制颜色代码定义颜色
        self.white_color = self.hex_to_rgb('#FFFFFF')
        self.red_color = self.hex_to_rgb('#FF1515')
        self.purple_color = self.hex_to_rgb('#A2A3FB')

    def hex_to_rgb(self, hex_color):
        """
        将十六进制颜色代码转换为 RGB 元组
        :param hex_color: 十六进制颜色代码 (例如: '#FF1515')
        :return: (r, g, b) 颜色值
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def get_region_bbox(self):
        """
        计算四个坐标点的最小边界框（bounding box）。
        :return: 最小边界框的 (left, top, right, bottom)
        """
        x_coords = [point[0] for point in self.points]
        y_coords = [point[1] for point in self.points]
        left = min(x_coords)
        top = min(y_coords)
        right = max(x_coords) + 1  # 增加1像素以确保包含边界
        bottom = max(y_coords) + 1  # 增加1像素以确保包含边界
        return (left, top, right, bottom)

    def get_region_image(self):
        """
        截取四个坐标点包围的最小区域的屏幕截图。
        :return: 截取区域的图像
        """
        bbox = self.get_region_bbox()
        screenshot = ImageGrab.grab(bbox=bbox)
        return screenshot

    def check_colors(self):
        """
        检查指定的所有像素点颜色
        :return: 当前检测到的颜色：'white', 'red', 'purple' 或 'mixed'
        """
        white_count = 0
        red_count = 0
        purple_count = 0

        bbox = self.get_region_bbox()
        region_img = self.get_region_image()

        pixels = np.array(region_img)

        # 检查每个点的颜色
        for idx, point in enumerate(self.points):
            relative_x = point[0] - bbox[0]  # 相对于截图区域左上角的 x 坐标
            relative_y = point[1] - bbox[1]  # 相对于截图区域左上角的 y 坐标

            # 添加边界检查，防止索引超出范围
            if 0 <= relative_x < pixels.shape[1] and 0 <= relative_y < pixels.shape[0]:
                color = tuple(pixels[relative_y, relative_x])
                # print(f"Point {point} color: {color}")  # 打印每个点的颜色

                if color == self.white_color:
                    white_count += 1
                elif color == self.red_color:
                    red_count += 1
                elif color == self.purple_color:
                    purple_count += 1
            else:
                print(f"Error: Point {point} is out of the captured region bounds.")

        if white_count == len(self.points):
            return 'white'
        elif red_count == len(self.points):
            return 'red'
        elif purple_count == len(self.points):
            return 'purple'
        else:
            return 'mixed'