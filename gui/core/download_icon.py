from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import requests

# 设置 ChromeOptions 以启用无头模式
chrome_options = Options()
chrome_options.add_argument("--headless")  # 无头模式
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("window-size=1920,1080")  # 设置窗口大小

# 设置 ChromeDriver 路径
service = Service(executable_path="../../chromedriver.exe")  # 替换为你的 chromedriver 路径
driver = webdriver.Chrome(service=service, options=chrome_options)

def download_icon(skill_name):
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

# 调用函数
download_icon("冲锋")

# 关闭浏览器
driver.quit()
