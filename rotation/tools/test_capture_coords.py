import cv2
import yaml
import numpy as np
from PIL import ImageGrab
import os

def load_config(config_file):
    """
    加载配置文件并返回截图区域的坐标。
    """
    if not os.path.exists(config_file):
        print(f"配置文件 {config_file} 不存在。")
        return None

    with open(config_file, 'r', encoding='utf-8') as file:
        try:
            config = yaml.safe_load(file)
            region_config = config.get('region', None)
            if region_config:
                return region_config
            else:
                print("配置文件中未找到截图区域信息。")
                return None
        except yaml.YAMLError as e:
            print(f"读取配置文件时出错: {e}")
            return None

def capture_screenshot(region):
    """
    根据提供的区域坐标截图。
    :param region: 字典，包含 x, y, width, height
    :return: 截图图像 (numpy 数组格式)
    """
    bbox = (region['x1'], region['y1'], region['x2'], region['y2'])
    screenshot = ImageGrab.grab(bbox=bbox)  # 截取指定区域
    screenshot_np = np.array(screenshot)  # 将截图转换为 numpy 数组
    screenshot_np = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)  # 转换为 OpenCV 的 BGR 格式
    return screenshot_np

def display_screenshot_with_region(screenshot, region):
    """
    显示截图并在指定区域绘制边框。
    :param screenshot: 截图图像 (numpy 数组格式)
    :param region: 字典，包含 x, y, width, height
    """
    # 在截图上绘制矩形，表示选定的区域
    top_left = (0, 0)
    bottom_right = (region['x2'], region['y2'])
    cv2.rectangle(screenshot, top_left, bottom_right, (0, 255, 0), 2)  # 绿色矩形框

    # 显示带边框的截图
    cv2.imshow("Selected Region", screenshot)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def main():
    # 配置文件路径
    config_file = '../rotation_config.yaml'

    # 加载配置文件中的截图区域
    region = load_config(config_file)
    if region is None:
        print("未加载到有效的截图区域。")
        return

    # 截取并显示截图区域
    screenshot = capture_screenshot(region)
    display_screenshot_with_region(screenshot, region)

if __name__ == "__main__":
    main()
