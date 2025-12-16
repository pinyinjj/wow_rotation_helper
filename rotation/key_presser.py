

import pyautogui
import random
import time


class KeyPresser:
    def __init__(self, config):
        """
        初始化按键处理器。

        参数：
        - config：配置参数。
        """
        self.min_delay = config['delay']['min']
        self.max_delay = config['delay']['max']
        self.set_random_delay()

    def set_random_delay(self):
        """
        设置按键之间的随机延迟。
        """
        self.delay = random.uniform(self.min_delay, self.max_delay)

    def press_key(self, key):
        """
        模拟按下一个键。

        参数：
        - key：要按下的键。
        """
        try:
            key = str(key)
            print(f"[Key Press] Pressing key: {key}", flush=True)
            pyautogui.press(key)
            time.sleep(self.delay)
            self.set_random_delay()
        except Exception as e:
            print(f"按键 {key} 时出错: {e}")
