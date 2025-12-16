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


    @staticmethod
    def _get_save_folder(class_name, talent_name, game_version):
        """获取保存文件夹路径"""
        if game_version.lower() == "classic":
            save_folder = os.path.join("gui", "uis", "icons", "classic", "talent_icons", class_name, talent_name)
        else:
            save_folder = os.path.join("gui", "uis", "icons", "talent_icons", class_name, talent_name)
        os.makedirs(save_folder, exist_ok=True)
        print(f"[DEBUG] 图标存储路径: {save_folder}")
        return save_folder
    
    @staticmethod
    def _get_versions_for_game(game_version):
        """根据游戏版本获取要尝试的版本列表"""
        if game_version.lower() == "classic":
            return [
                ("classic", "https://www.wowhead.com/classic"),
                ("tbc", "https://www.wowhead.com/tbc"),
                ("wotlk", "https://www.wowhead.com/wotlk")
            ]
        else:
            return [("retail", "https://www.wowhead.com")]
    
    @staticmethod
    def _get_url_path(item_type, item_id):
        """构建URL路径"""
        if item_type == 'spell':
            return f"/spell={item_id}"
        else:  # item (trinket or consumable)
            return f"/item={item_id}"
    
    @staticmethod
    def _has_multiple_types(spell_id, trinket_id, consumable_id):
        """检查是否有多个类型的ID"""
        return sum([
            spell_id is not None,
            trinket_id is not None,
            consumable_id is not None
        ]) > 1
    
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
        save_folder = Functions._get_save_folder(class_name, talent_name, game_version)

    @staticmethod
    async def _fetch_icon_async(page, url, item_id, item_type='spell'):
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
                return (1, icon_url, item_name)
            else:
                print(f"[DEBUG] 未找到图标链接或物品名称: {item_id}, icon_url: {icon_url}, item_name: {item_name}")
                return (-3, None, None)
        except Exception as e:
            print(f"[ERROR] Exception in fetch_icon for {item_id} at {url}: {e}")
            return (-1, None, None)
    
    @staticmethod
    async def _fetch_version_icon(version_name, base_url, url_path, item_id, item_type):
        """异步获取图标"""
        url = f"{base_url}{url_path}"
        print(f"[DEBUG] [异步任务 {version_name}] 尝试版本: {version_name}, URL: {url}")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                try:
                    status, icon_url, item_name = await Functions._fetch_icon_async(page, url, item_id, item_type)
                    
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
    
    @staticmethod
    async def _try_multiple_versions_async(item_id, item_type='spell', game_version=''):
        """
        异步尝试多个版本的链接：classic -> tbc -> wotlk -> retail
        任何一个成功就取消其他任务
        返回: (status, icon_url, item_name, used_version)
        """
        versions = Functions._get_versions_for_game(game_version)
        url_path = Functions._get_url_path(item_type, item_id)

        # 创建所有异步任务
        tasks = [
            asyncio.create_task(Functions._fetch_version_icon(version_name, base_url, url_path, item_id, item_type))
            for version_name, base_url in versions
        ]
        
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
    
    @staticmethod
    def _try_multiple_versions(item_id, item_type='spell', game_version=''):
        """同步包装器，调用异步函数"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(Functions._try_multiple_versions_async(item_id, item_type, game_version))

    @staticmethod
    def _download_and_save(icon_url, item_name, item_id, save_folder):
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

    @staticmethod
    async def _try_all_types_async(spell_id, trinket_id, consumable_id, game_version):
        """同时尝试所有类型的ID"""
        tasks = []
        task_info = []  # 存储任务信息 (item_type, item_id)
        
        if spell_id is not None:
            async def try_spell():
                return await Functions._try_multiple_versions_async(spell_id, 'spell', game_version)
            tasks.append(asyncio.create_task(try_spell()))
            task_info.append(('spell', spell_id))
        
        if trinket_id is not None:
            async def try_trinket():
                return await Functions._try_multiple_versions_async(trinket_id, 'item', game_version)
            tasks.append(asyncio.create_task(try_trinket()))
            task_info.append(('trinket', trinket_id))
        
        if consumable_id is not None:
            async def try_consumable():
                return await Functions._try_multiple_versions_async(consumable_id, 'item', game_version)
            tasks.append(asyncio.create_task(try_consumable()))
            task_info.append(('consumable', consumable_id))
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        success_count = 0
        success_info = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"[ERROR] Exception in {task_info[i][0]} {task_info[i][1]}: {result}")
                continue
            
            if result and result[0] == 1:
                success_count += 1
                success_info.append({
                    'type': task_info[i][0],
                    'id': task_info[i][1],
                    'icon_url': result[1],
                    'item_name': result[2]
                })
        
        return success_count, success_info
    
    @staticmethod
    def _process_classic_multiple_types(spell_id, trinket_id, consumable_id, game_version, save_folder):
        """处理classic模式下多个类型的ID"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        success_count, success_info = loop.run_until_complete(
            Functions._try_all_types_async(spell_id, trinket_id, consumable_id, game_version)
        )
        
        if success_count > 1:
            success_types = [info['type'] for info in success_info]
            print(f"[INFO] 多个链接找到图标: {success_types}，返回选择列表")
            return {
                'multiple_icons': True,
                'icons': success_info
            }
        elif success_count == 1:
            info = success_info[0]
            download_status = Functions._download_and_save(
                info['icon_url'],
                info['item_name'],
                info['id'],
                save_folder
            )
            return download_status
        else:
            return -3
    
    @staticmethod
    def _process_single_type_download(spell_id, trinket_id, consumable_id, game_version, save_folder):
        """处理单个类型的下载"""
        results = []
        
        if spell_id is not None:
            status, icon_url, item_name, _ = Functions._try_multiple_versions(
                spell_id, 'spell', game_version
            )
            if status == 1:
                download_status = Functions._download_and_save(icon_url, item_name, spell_id, save_folder)
                results.append(download_status)
            else:
                results.append(status)
        
        if trinket_id is not None:
            status, icon_url, item_name, _ = Functions._try_multiple_versions(
                trinket_id, 'item', game_version
            )
            if status == 1:
                download_status = Functions._download_and_save(icon_url, item_name, trinket_id, save_folder)
                results.append(download_status)
            else:
                results.append(status)
        
        if consumable_id is not None:
            status, icon_url, item_name, _ = Functions._try_multiple_versions(
                consumable_id, 'item', game_version
            )
            if status == 1:
                download_status = Functions._download_and_save(icon_url, item_name, consumable_id, save_folder)
                results.append(download_status)
            else:
                results.append(status)

        if len(results) == 0:
            print("[ERROR] No valid IDs provided")
            return -1
        return results[0] if len(results) == 1 else results
    
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
        save_folder = Functions._get_save_folder(class_name, talent_name, game_version)
        
        try:
            is_classic = game_version.lower() == "classic"
            has_multiple_types = Functions._has_multiple_types(spell_id, trinket_id, consumable_id)
            
            if is_classic and has_multiple_types:
                return Functions._process_classic_multiple_types(
                    spell_id, trinket_id, consumable_id, game_version, save_folder
                )
            else:
                return Functions._process_single_type_download(
                    spell_id, trinket_id, consumable_id, game_version, save_folder
                )
        except Exception as e:
            print(f"[ERROR] Exception in download_icon: {e}")
            import traceback
            traceback.print_exc()
            return -1

    @staticmethod
    def _sanitize_filename(name):
        """清理文件名，只保留字母数字和下划线"""
        return "".join(c if c.isalnum() else "_" for c in name)
    
    @staticmethod
    def _get_file_extension(icon_url):
        """从URL中提取文件扩展名"""
        return icon_url.split('.')[-1].split('?')[0]
    
    @staticmethod
    def download_and_save_icon(icon_url, item_name, item_id, class_name='', talent_name='', game_version=''):
        """
        直接下载并保存图标（用于用户选择后的保存）
        
        参数:
            icon_url (str): 图标URL
            item_name (str): 物品名称
            item_id (int): 物品ID
            class_name (str): 职业名称
            talent_name (str): 天赋名称
            game_version (str): 游戏版本
        """
        save_folder = Functions._get_save_folder(class_name, talent_name, game_version)
        
        try:
            sanitized_name = Functions._sanitize_filename(item_name)
            file_extension = Functions._get_file_extension(icon_url)
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
            print(f"[ERROR] Exception in download_and_save_icon for {item_id}: {e}")
            import traceback
            traceback.print_exc()
            return -1





