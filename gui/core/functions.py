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

    def download_icon(skill_name, class_name, talent_name):
        # Set up the directory relative to the project root
        save_folder = os.path.join("gui", "uis", "icons", "talent_icons", class_name, talent_name)

        # Ensure the directory exists
        os.makedirs(save_folder, exist_ok=True)
        print(f"Directory verified for saving icons: {save_folder}")

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("window-size=1920,1080")

        # Set the correct path for chromedriver relative to this file's location
        chromedriver_path = os.path.join(os.path.dirname(__file__), "../../chromedriver.exe")
        print(f"Attempting to use chromedriver at: {chromedriver_path}")

        try:
            service = Service(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # Construct and navigate to the URL
            url = f'https://www.wowhead.com/cn/spells/abilities/name:{skill_name}'
            driver.get(url)

            # Execute JavaScript to fetch the icon URL
            icon_url = driver.execute_script('''
                const iconElement = document.querySelector("ins");
                if (iconElement && iconElement.style.backgroundImage) {
                    return iconElement.style.backgroundImage.slice(5, -2).replace('/medium/', '/large/');
                }
                return null;
            ''')

            if icon_url:
                # Determine file extension and save path
                file_extension = icon_url.split('.')[-1]
                icon_path = os.path.join(save_folder, f"{skill_name}.{file_extension}")
                print(f"Saving icon to: {icon_path}")

                # Download the icon
                response = requests.get(icon_url)
                if response.status_code == 200:
                    with open(icon_path, 'wb') as f:
                        f.write(response.content)
                    print(f"Icon successfully downloaded and saved at: {icon_path}")

                    # Verify file existence and size
                    if os.path.exists(icon_path) and os.path.getsize(icon_path) > 0:
                        return 1  # Success
                    else:
                        print("Error: File not saved correctly")
                        return -2  # Error: File not saved correctly
                else:
                    print("Error: Failed to download icon")
                    return -1  # Error: Failed to download icon
            else:
                print("Error: Icon link not found")
                return -3  # Error: Icon link not found

        except Exception as e:
            print(f"Exception during download: {e}")
            return -4  # Error: Exception occurred (e.g., Chrome driver error)

        finally:
            # Ensure that driver.quit() is always called
            print("Closing the driver.")
            driver.quit()

