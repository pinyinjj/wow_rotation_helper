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
import asyncio
from playwright.async_api import async_playwright
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

        async def fetch_icon_async(page, url, item_id, item_type='spell'):
            """
            异步尝试从指定URL获取图标
            返回: (status, icon_url, item_name)
            status: 1=成功, -1=网络错误, -3=未找到图标
            """
            try:
                print(f"[DEBUG] Fetching icon from URL: {url}")
                await page.goto(url, timeout=30000)

                # 模拟滚动以加载动态内容
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(2000)  # 等待页面加载

                # 提取图标 URL 和项目名称
                icon_url = await page.evaluate('''() => {
                    const insElement = document.querySelector('ins[style*="background-image"][style*="large"]');
                    return insElement ? insElement.style.backgroundImage.slice(5, -2) : null;
                }''')

                item_name = await page.evaluate('''() => {
                    const heading = document.querySelector('h1.heading-size-1');
                    return heading ? heading.innerText.trim() : null;
                }''')

                print(f"[DEBUG] Extracted icon_url: {icon_url}, item_name: {item_name}")

                if icon_url and item_name and item_name != "Classic Spells":
                    # 检查是否找到了有效的图标和名称
                    return (1, icon_url, item_name)
                else:
                    print(f"[DEBUG] 未找到图标链接或物品名称: {item_id}, icon_url: {icon_url}, item_name: {item_name}")
                    return (-3, None, None)
            except Exception as e:
                print(f"[ERROR] Exception in fetch_icon for {item_id} at {url}: {e}")
                return (-1, None, None)

        async def try_multiple_versions_async(item_id, item_type='spell', game_version=''):
            """
            异步尝试多个版本的链接：classic -> tbc -> wotlk -> retail
            任何一个成功就取消其他任务
            返回: (status, icon_url, item_name, used_version)
            """
            # 根据game_version确定尝试顺序
            if game_version.lower() == "classic":
                # classic版本只尝试classic相关版本，不尝试retail
                versions = [
                    ("classic", "https://www.wowhead.com/classic"),
                    ("tbc", "https://www.wowhead.com/tbc"),
                    ("wotlk", "https://www.wowhead.com/wotlk")
                ]
            else:
                # retail版本只尝试retail，不尝试classic相关版本
                versions = [("retail", "https://www.wowhead.com")]

            # 构建URL路径
            if item_type == 'spell':
                url_path = f"/spell={item_id}"
            else:  # item (trinket or consumable)
                url_path = f"/item={item_id}"

            async def fetch_version_icon(version_name, base_url):
                """异步获取图标"""
                url = f"{base_url}{url_path}"
                print(f"[DEBUG] [异步任务 {version_name}] 尝试版本: {version_name}, URL: {url}")
                
                try:
                    async with async_playwright() as p:
                        browser = await p.chromium.launch(headless=True)
                        page = await browser.new_page()
                        
                        try:
                            status, icon_url, item_name = await fetch_icon_async(page, url, item_id, item_type)
                            
                            if status == 1:
                                print(f"[INFO] [异步任务 {version_name}] 在 {version_name} 版本找到图标")
                                return (1, icon_url, item_name, version_name)
                            else:
                                print(f"[DEBUG] [异步任务 {version_name}] 版本 {version_name} 未找到图标")
                                return None
                        finally:
                            await browser.close()
                except Exception as e:
                    print(f"[ERROR] [异步任务 {version_name}] 异常: {e}")
                    return None

            # 创建所有异步任务
            tasks = [asyncio.create_task(fetch_version_icon(version_name, base_url)) 
                    for version_name, base_url in versions]
            
            # 使用 as_completed 等待第一个成功的任务
            for coro in asyncio.as_completed(tasks):
                try:
                    result = await coro
                    if result and result[0] == 1:
                        # 取消其他未完成的任务
                        for task in tasks:
                            if not task.done():
                                task.cancel()
                        # 等待所有任务完成（包括取消的）
                        await asyncio.gather(*tasks, return_exceptions=True)
                        return result
                except asyncio.CancelledError:
                    continue
            
            # 所有版本都失败了
            print(f"[ERROR] 所有版本都未找到图标: {item_id}")
            return (-3, None, None, None)
        
        def try_multiple_versions(item_id, item_type='spell', game_version=''):
            """
            同步包装器，调用异步函数
            """
            try:
                # 尝试获取当前事件循环
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # 如果没有事件循环，创建一个新的
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # 运行异步函数
            return loop.run_until_complete(try_multiple_versions_async(item_id, item_type, game_version))

        def download_and_save(icon_url, item_name, item_id):
            """下载并保存图标"""
            try:
                sanitized_name = "".join(c if c.isalnum() else "_" for c in item_name)
                file_extension = icon_url.split('.')[-1].split('?')[0]  # Remove query parameters
                icon_path = os.path.join(save_folder, f"{sanitized_name}.{file_extension}")

                print(f"[DEBUG] Downloading icon from: {icon_url}")
                response = requests.get(icon_url, timeout=10)
                if response.status_code == 200:
                    with open(icon_path, 'wb') as f:
                        f.write(response.content)
                    print(f"[INFO] 图标下载成功: {icon_path}")
                    return 1
                else:
                    print(f"[ERROR] 下载失败，HTTP状态码: {response.status_code}, item_id: {item_id}")
                    return -1
            except Exception as e:
                print(f"[ERROR] Exception in download_and_save for {item_id}: {e}")
                return -1

        try:
            results = []
            if spell_id is not None:
                status, icon_url, item_name, used_version = try_multiple_versions(
                    spell_id, 'spell', game_version
                )
                if status == 1:
                    download_status = download_and_save(icon_url, item_name, spell_id)
                    results.append(download_status)
                else:
                    results.append(status)
            
            if trinket_id is not None:
                status, icon_url, item_name, used_version = try_multiple_versions(
                    trinket_id, 'item', game_version
                )
                if status == 1:
                    download_status = download_and_save(icon_url, item_name, trinket_id)
                    results.append(download_status)
                else:
                    results.append(status)
            
            if consumable_id is not None:
                status, icon_url, item_name, used_version = try_multiple_versions(
                    consumable_id, 'item', game_version
                )
                if status == 1:
                    download_status = download_and_save(icon_url, item_name, consumable_id)
                    results.append(download_status)
                else:
                    results.append(status)

            # 返回单一结果或结果列表
            if len(results) == 0:
                print("[ERROR] No valid IDs provided")
                return -1
            return results[0] if len(results) == 1 else results
        except Exception as e:
            print(f"[ERROR] Exception in download_icon: {e}")
            import traceback
            traceback.print_exc()
            return -1





