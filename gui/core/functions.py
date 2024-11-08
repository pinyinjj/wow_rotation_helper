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

    def set_gif(gif_name):
        app_path = os.path.abspath(os.getcwd())
        folder = "gui/images/gifs/"
        path = os.path.join(app_path, folder)
        gif = os.path.normpath(os.path.join(path, gif_name))
        return gif

    def download_icon(skill_id=None, trinket_id=None, consumable_id=None, class_name='', talent_name=''):
        driver = None
        save_folder = os.path.join("gui", "uis", "icons", "talent_icons", class_name, talent_name)
        os.makedirs(save_folder, exist_ok=True)
        print(f"Directory verified for saving icons: {save_folder}")

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("window-size=1920,1080")
        chromedriver_path = os.path.join(os.path.dirname(__file__), "../../chromedriver.exe")
        print(f"Attempting to use chromedriver at: {chromedriver_path}")

        def fetch_icon(driver, url, item_id):
            driver.get(url)

            icon_url = driver.execute_script('''
                const insElement = document.querySelector('ins[style*="background-image"][style*="large"]');
                return insElement ? insElement.style.backgroundImage.slice(5, -2) : null;
            ''')

            item_name = driver.execute_script('''
                const heading = document.querySelector('h1.heading-size-1');
                return heading ? heading.innerText.trim() : null;
            ''')

            if icon_url and item_name:
                sanitized_name = "".join(c if c.isalnum() else "_" for c in item_name)
                file_extension = icon_url.split('.')[-1]
                icon_path = os.path.join(save_folder, f"{sanitized_name}.{file_extension}")

                response = requests.get(icon_url)
                if response.status_code == 200:
                    with open(icon_path, 'wb') as f:
                        f.write(response.content)
                    print(f"Icon successfully downloaded and saved as: {icon_path}")
                    return 1
                else:
                    print(f"Error: Failed to download icon for {item_id}")
                    return -1
            else:
                print(f"Error: Icon link or item name not found for {item_id}")
                return -3

        try:
            service = Service(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)

            results = []
            if skill_id:
                results.append(fetch_icon(driver, f'https://www.wowhead.com/spell={skill_id}', skill_id))
            if trinket_id:
                results.append(fetch_icon(driver, f'https://www.wowhead.com/item={trinket_id}', trinket_id))
            if consumable_id:
                results.append(fetch_icon(driver, f'https://www.wowhead.com/item={consumable_id}', consumable_id))

            # Return a single value if only one ID was provided; otherwise, return the list of results
            return results[0] if len(results) == 1 else results

        except Exception as e:
            print(f"Exception during download: {e}")
            return -4

        finally:
            print("Closing the driver.")
            if driver:
                driver.quit()



