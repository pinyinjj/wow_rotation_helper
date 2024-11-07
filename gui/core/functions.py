# ///////////////////////////////////////////////////////////////
#
# BY: WANDERSON M.PIMENTA
# PROJECT MADE WITH: Qt Designer and PySide6
# V: 1.0.0
#
# This project can be used freely for all uses, as long as they maintain the
# respective credits only in the Python scripts, any information in the visual
# interface (GUI) can be modified without any implication.
#
# There are limitations on Qt licenses if you want to use your products
# commercially, I recommend reading them on the official website:
# https://doc.qt.io/qtforpython/licenses.html
#
# ///////////////////////////////////////////////////////////////

# IMPORT PACKAGES AND MODULES
# ///////////////////////////////////////////////////////////////
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import requests
# APP FUNCTIONS
# ///////////////////////////////////////////////////////////////
class Functions:

    # SET SVG ICON
    # ///////////////////////////////////////////////////////////////
    def set_svg_icon(icon_name):
        app_path = os.path.abspath(os.getcwd())
        folder = "gui/images/svg_icons/"
        path = os.path.join(app_path, folder)
        icon = os.path.normpath(os.path.join(path, icon_name))
        return icon

    # SET SVG IMAGE
    # ///////////////////////////////////////////////////////////////
    def set_svg_image(icon_name):
        app_path = os.path.abspath(os.getcwd())
        folder = "gui/images/svg_images/"
        path = os.path.join(app_path, folder)
        icon = os.path.normpath(os.path.join(path, icon_name))
        return icon

    # SET IMAGE
    # ///////////////////////////////////////////////////////////////
    def set_image(image_name):
        app_path = os.path.abspath(os.getcwd())
        folder = "gui/images/images/"
        path = os.path.join(app_path, folder)
        image = os.path.normpath(os.path.join(path, image_name))
        return image

    def download_icon(skill_name):
        # 设置 ChromeOptions 以启用无头模式
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 无头模式
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("window-size=1920,1080")  # 设置窗口大小

        # 设置 ChromeDriver 路径
        service = Service(executable_path="../../chromedriver.exe")  # 替换为你的 chromedriver 路径
        driver = webdriver.Chrome(service=service, options=chrome_options)

        url = f'https://www.wowhead.com/cn/spells/abilities/name:{skill_name}'
        driver.get(url)

        # 使用 JavaScript 获取图标链接
        icon_url = driver.execute_script('''
            const iconElement = document.querySelector("ins");  // 选择图标元素
            if (iconElement && iconElement.style.backgroundImage) {
                // 提取背景图 URL 并返回
                return iconElement.style.backgroundImage.slice(5, -2).replace('/medium/', '/large/');
            }
            return null;
        ''')

        if icon_url:
            # 获取文件扩展名
            file_extension = icon_url.split('.')[-1]

            # 下载并保存图标
            with open(f'{skill_name}.{file_extension}', 'wb') as f:
                f.write(requests.get(icon_url).content)
            print(f'图标已成功下载并保存为 {skill_name}.{file_extension}')
        else:
            print('未找到图标链接')

        # 关闭浏览器
        driver.quit()