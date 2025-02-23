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
import time
import os
from playwright.sync_api import sync_playwright
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

    def set_gif(gif_name):
        app_path = os.path.abspath(os.getcwd())
        folder = "gui/images/gifs/"
        path = os.path.join(app_path, folder)
        gif = os.path.normpath(os.path.join(path, gif_name))
        return gif

    import os
    import requests
    from playwright.sync_api import sync_playwright

    def download_icon(spell_id=None, trinket_id=None, consumable_id=None, class_name='', talent_name='',
                      game_version=''):
        """
        下载技能、饰品或消耗品的图标，并保存到指定目录。

        参数:
            spell_id (int): 技能 ID
            trinket_id (int): 饰品 ID
            consumable_id (int): 消耗品 ID
            class_name (str): 职业名称（用于文件夹分类）
            talent_name (str): 天赋名称（用于文件夹分类）
            game_version (str): 游戏版本，可选 'retail'（默认）或 'classic'
        """
        # ✅ 只在 Classic 版本下添加 'classic' 文件夹
        if game_version.lower() == "classic":
            save_folder = os.path.join("gui", "uis", "icons", "classic", "talent_icons", class_name, talent_name)
        else:
            save_folder = os.path.join("gui", "uis", "icons", "talent_icons", class_name, talent_name)

        os.makedirs(save_folder, exist_ok=True)
        print(f"[DEBUG] 图标存储路径: {save_folder}")

        # 确定 URL 前缀
        base_url = "https://www.wowhead.com"
        if game_version.lower() == "classic":
            base_url = "https://www.wowhead.com/classic"

        def fetch_icon(page, url, item_id):
            page.goto(url)

            # 模拟滚动以加载动态内容
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_timeout(2000)  # 等待页面加载

            # 提取图标 URL 和项目名称
            icon_url = page.evaluate('''() => {
                const insElement = document.querySelector('ins[style*="background-image"][style*="large"]');
                return insElement ? insElement.style.backgroundImage.slice(5, -2) : null;
            }''')

            item_name = page.evaluate('''() => {
                const heading = document.querySelector('h1.heading-size-1');
                return heading ? heading.innerText.trim() : null;
            }''')

            if icon_url and item_name:
                sanitized_name = "".join(c if c.isalnum() else "_" for c in item_name)
                file_extension = icon_url.split('.')[-1]
                icon_path = os.path.join(save_folder, f"{sanitized_name}.{file_extension}")

                response = requests.get(icon_url)
                if response.status_code == 200:
                    with open(icon_path, 'wb') as f:
                        f.write(response.content)
                    print(f"[INFO] 图标下载成功: {icon_path}")
                    return 1
                else:
                    print(f"[ERROR] 下载失败: {item_id}")
                    return -1
            else:
                print(f"[ERROR] 未找到图标链接或物品名称: {item_id}")
                return -3

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            results = []
            if spell_id:
                results.append(fetch_icon(page, f'{base_url}/spell={spell_id}', spell_id))
            if trinket_id:
                results.append(fetch_icon(page, f'{base_url}/item={trinket_id}', trinket_id))
            if consumable_id:
                results.append(fetch_icon(page, f'{base_url}/item={consumable_id}', consumable_id))

            browser.close()

            # 返回单一结果或结果列表
            return results[0] if len(results) == 1 else results





