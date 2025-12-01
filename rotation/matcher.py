import cv2
import numpy as np
import os
import time
from PIL import ImageGrab
import pygetwindow as gw
from datetime import datetime
from gui.core.json_settings import Settings
from .key_presser import KeyPresser
from .template_matcher import TemplateMatcher


class ImageMatcher:
    def __init__(self, icon_templates, key_mapping, config, version):
        """
        初始化图像匹配器。

        参数：
        - icon_templates：图标模板字典。
        - key_mapping：按键映射字典。
        - config：配置参数。
        """
        # 原始图标模板：name -> 图像
        self.icon_templates = icon_templates
        self.key_mapping = key_mapping
        self.key_presser = KeyPresser(config)
        self.screenshot_delay = config['screenshot_delay']

        # HDR 亮度压暗系数（可通过配置控制，范围建议 0.1 - 1.0）
        self.hdr_darkness = float(config.get("hdr_darkness", 0.3))

        # 与 GUI 预览使用的 zoom/template_scale 保持一致
        self.zoom = float(config.get("zoom", 1.0))

        self.settings = Settings()
        if version == 'retail':
            self.threshhold = self.settings.items.get("retail_threshold", 0.5)
        elif version == 'classic':
            self.threshhold = self.settings.items.get("classic_threshold", 0.3)
        print(self.threshhold)
        region_config = config['region']
        self.last_match = None
        self.region = (
            region_config['x1'],
            region_config['y1'],
            region_config['x2'],
            region_config['y2']
        )
        self.running = True
        self.manual_pause = False  # 手动暂停标志
        self.match_callback = None  # Callback function for when icon is matched
        self.frame_callback = None  # Callback function for previewing each frame
        self.cast_time_skills = {
            '20241030222919': 4,
        }
        # 预构建模板彩色缓存，匹配方式参考 example/main.py 的模板缓存思路
        self.template_cache = self._build_template_cache()
        # 是否允许在匹配成功时执行按键输入（由 RotationHelper 控制）
        self.enable_keys = True

    def _apply_hdr_correction(self, frame_bgr):
        """
        针对开启 HDR 时截图偏亮的问题，对截图做「色调映射」而不是简单整体变暗。

        目标：尽可能还原原图的色彩观感，而不是一刀切地调低亮度。

        实现思路（全局色调映射，近似保留颜色）：
        - 先将 BGR 转为线性 RGB 浮点 [0, 1]
        - 计算物理意义上的亮度 Y = 0.2126 R + 0.7152 G + 0.0722 B
        - 对 Y 做一个类似 Reinhard 的压缩：Y' = Y / (1 + Y)
          * 低中亮度几乎不变，高光被平滑压缩，避免「一片白」
        - 用比例因子 scale = Y' / (Y + eps) 去缩放每个像素的 RGB：
          * 这样保持 R:G:B 的比例基本不变，颜色不易偏色
        - 再转换回 8bit BGR

        注意：HDR → SDR 本质是有损的，本实现只是尽量贴近 SDR 显示器上的观感。
        亮度压暗系数从配置中的 `hdr_darkness` 读取，默认 0.3。
        """
        # 直接委托给公共封装，确保与其他模块（如 CapturePage、ClassPage 预览）保持一致
        return TemplateMatcher.apply_hdr_correction(frame_bgr, dark_factor=self.hdr_darkness)

    def _build_template_cache(self):
        """
        将所有图标模板预处理为彩色图并缓存，供匹配阶段直接使用。

        （保留旧逻辑以兼容，但实际匹配将使用灰度+缩放公共函数）
        """
        cache = {}
        for name, icon_template in self.icon_templates.items():
            if icon_template is None:
                continue
            try:
                # 统一为 BGR 彩色图像
                if len(icon_template.shape) == 3:
                    # 可能是 BGR 或 BGRA，这里强制转为 BGR
                    if icon_template.shape[2] == 4:
                        tmpl_color = cv2.cvtColor(icon_template, cv2.COLOR_BGRA2BGR)
                    else:
                        tmpl_color = icon_template.copy()
                elif len(icon_template.shape) == 2:
                    # 灰度模板转为 BGR
                    tmpl_color = cv2.cvtColor(icon_template, cv2.COLOR_GRAY2BGR)
                else:
                    continue
                h, w = tmpl_color.shape[:2]
                if h == 0 or w == 0:
                    continue
                cache[name] = {
                    "tmpl_color": tmpl_color,
                    "height": h,
                    "width": w,
                }
            except Exception as e:
                print(f"构建模板缓存时出错 {name}: {e}", flush=True)
        return cache

    @staticmethod
    def match_best_icon_with_scale(frame_bgr, templates_dict, scale):
        """
        公共匹配函数：内部委托给 `TemplateMatcher.match_best_icon_with_scale`。
        保留此静态方法以兼容现有调用方。
        """
        return TemplateMatcher.match_best_icon_with_scale(frame_bgr, templates_dict, scale)

    def set_match_callback(self, callback):
        """Set callback function to be called when an icon is matched."""
        self.match_callback = callback

    def set_frame_callback(self, callback):
        """Set callback for per-frame preview (screenshot + best match info)."""
        self.frame_callback = callback

    def is_cast_time_skill(self, key):
        """
        判断技能是否有施法时间。

        参数：
        - key：技能名称。

        返回：
        - 布尔值，表示是否有施法时间。
        - 施法时间（秒）。
        """
        if key in self.cast_time_skills:
            return True, self.cast_time_skills[key]
        return False, 0

    def resize_template(self, template, target_size):
        """
        将模板图像调整到指定尺寸。

        参数：
        - template：模板图像。
        - target_size：目标尺寸。

        返回：
        - 调整后的模板图像。
        """
        h_template, w_template = template.shape[:2]
        h_target, w_target = target_size
        if h_template != h_target or w_template != w_target:
            resized_template = cv2.resize(template, (w_target, h_target))
            return resized_template
        return template

    def take_screenshot(self):
        """
        截取屏幕的指定区域，并将图像从 RGB 转换为 BGR。
        """
        active_window = gw.getActiveWindow()
        if active_window and "魔兽世界" in active_window.title:
            try:
                screenshot = ImageGrab.grab(bbox=self.region)
                screenshot_np = np.array(screenshot)  # 这是 RGB 格式的图像 (HDR 显示下可能偏亮)
                # 将图像从 RGB 转换为 BGR
                screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

                # 针对 HDR 做一次亮度压缩，避免画面过亮影响匹配
                screenshot_bgr = self._apply_hdr_correction(screenshot_bgr)
                return screenshot_bgr  # 返回 BGR 格式的图像
            except Exception as e:
                print(f"Failed to take screenshot: {e}", flush=True)
                return None
        else:
            time.sleep(1)
            print("窗口未激活，不截图", flush=True)
            return None

    def show_comparison(self, screenshot_color, template_color, template_name, match_value, top_left):
        """
        显示模板和截图的对比，以及它们之间的差异（彩色）。

        参数：
        - screenshot_color：截取的屏幕彩色图像（BGR 格式）。
        - template_color：模板彩色图像（BGR 格式）。
        - template_name：模板名称。
        - match_value：匹配得分。
        - top_left：匹配位置的左上角坐标。
        """
        h, w = template_color.shape[:2]

        # 在截图上绘制匹配区域
        screenshot_copy = screenshot_color.copy()
        cv2.rectangle(screenshot_copy, top_left, (top_left[0] + w, top_left[1] + h), (0, 255, 0), 2)
        cv2.putText(screenshot_copy, f"{template_name}: {match_value:.2f}", (top_left[0], top_left[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # 裁剪出匹配区域的图像
        matched_region = screenshot_color[top_left[1]:top_left[1] + h, top_left[0]:top_left[0] + w]

        # 检查裁剪是否超出图像边界
        if matched_region.shape[0] != h or matched_region.shape[1] != w:
            print("匹配区域大小与模板不一致，跳过显示。")
            return

        # 计算模板和匹配区域的差异（在彩色空间进行）
        diff = cv2.absdiff(template_color, matched_region)
        # 放大差异以增强可视化效果
        diff = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)

        # 将模板、匹配区域和差异拼接在一起
        comparison = np.hstack((template_color, matched_region, diff))

        # 调整窗口大小以适应图像
        cv2.namedWindow('模板 vs 匹配区域 vs 差异', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('模板 vs 匹配区域 vs 差异', 900, 300)
        cv2.imshow('模板 vs 匹配区域 vs 差异', comparison)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def handler_result(self, match_result):
        """
        根据最佳匹配结果执行相应操作。

        参数：
        - match_result: 一个元组 (best_match, best_match_value)
        """
        active_window = gw.getActiveWindow()
        if active_window and "魔兽世界" in active_window.title:
            if match_result is not None:
                best_match, score = match_result

                # 调试输出：无论是否超过阈值，都打印当前最佳匹配及得分
                try:
                    print(
                        f"[DEBUG] 最佳匹配: {best_match}, 得分: {score:.3f}, 当前阈值: {self.threshhold:.3f}",
                        flush=True,
                    )
                except Exception:
                    pass

                # 当技能名称为 Battle_Shout 时，减少分值 0.15 以防止识别错误
                if best_match == "Battle_Shout":
                    score -= 0.15

                # 针对部分技能使用更宽松的阈值（例如某些增益类技能图标对比度较低）
                # Tiger_s_Fury / Mark_of_the_Wild / Swipe__Cat_ 使用 0.4 阈值，其它技能使用默认阈值
                effective_threshold = self.threshhold
                if isinstance(best_match, str) and best_match in ("Tiger_s_Fury", "Mark_of_the_Wild", "Swipe__Cat_"):
                    effective_threshold = 0.4

                # 达到对应阈值才执行后续逻辑，否则只打印调试信息
                if score > effective_threshold:
                    if isinstance(best_match, str):
                        if best_match in self.key_mapping:
                            if self.enable_keys:
                                # 运行模式：真正执行按键
                                self.process_skill_action(best_match, score)
                            else:
                                # 预览模式：只通知 GUI 高亮，不执行按键
                                if self.last_match != best_match:
                                    self.last_match = best_match
                                    if self.match_callback:
                                        self.match_callback(best_match)
                        else:
                            print(f"[DEBUG] 按键映射中未找到键 '{best_match}'，不执行按键。", flush=True)
                    else:
                        print("[DEBUG] 最佳匹配不是字符串，跳过输入。", flush=True)
                else:
                    print("[DEBUG] 得分未达到阈值，不执行按键。", flush=True)
            else:
                print("[DEBUG] 未找到匹配项。", flush=True)
        else:
            print("魔兽世界窗口未聚焦，跳过输入。", flush=True)


    def process_skill_action(self, best_match, score):
        """
        处理技能动作。

        参数：
        - best_match：最佳匹配的技能名称。
        """
        shortcut = self.get_skill_info(best_match)
        needs_cast_time, cast_time = self.is_cast_time_skill(best_match)

        if self.last_match != best_match:
            self.log_skill_usage(best_match, shortcut, score)
            self.last_match = best_match
            # Call callback to notify GUI about matched icon
            if self.match_callback:
                self.match_callback(best_match)

        if needs_cast_time:
            self.execute_skill_with_cast(shortcut, cast_time, best_match)
        else:
            self.key_presser.press_key(shortcut)

    def get_skill_info(self, icon_name):
        """
        获取技能的快捷键信息。

        参数：
        - icon_name：技能图标名称。

        返回：
        - 技能对应的快捷键。
        """
        shortcut = self.key_mapping.get(icon_name, '未知按键')
        return shortcut

    def execute_skill_with_cast(self, shortcut, cast_time):
        """
        执行有施法时间的技能。

        参数：
        - shortcut：技能快捷键。
        - cast_time：施法时间。
        - icon_name：技能图标名称。
        """
        start_time = time.time()
        end_time = start_time + cast_time

        while time.time() < end_time:
            remaining_time = end_time - time.time()
            if remaining_time + 1 > 1.0:
                self.key_presser.press_key(shortcut)

    def log_skill_usage(self, icon_name, shortcut, score):
        """
        记录技能使用日志。

        参数：
        - icon_name：技能图标名称。
        - shortcut：技能快捷键。
        - score：匹配得分。
        """
        print(f"{time.strftime('%H:%M:%S')} 按下“{shortcut}” 使用“{icon_name}”，匹配得分 {score:.2f}", flush=True)
        print("-----------------------", flush=True)

    def _match_templates_on_frame(self, screenshot):
        """
        使用与 GUI 预览一致的灰度 + 模板缩放算法，在单帧截图上做模板匹配。
        """
        if screenshot is None:
            print("未提供截图。", flush=True)
            return None, None, -1.0

        # 统一将截图转为 BGR 彩色图像进行匹配
        try:
            if len(screenshot.shape) == 3:
                frame_bgr = screenshot
            elif len(screenshot.shape) == 2:
                frame_bgr = cv2.cvtColor(screenshot, cv2.COLOR_GRAY2BGR)
            else:
                return None, None, -1.0
        except Exception as e:
            print(f"转换截图为 BGR 图时出错: {e}", flush=True)
            return None, None, -1.0

        # 使用公共匹配逻辑（与预览共用），模板来源于 icon_templates
        best_name, best_img_info, best_score = self.match_best_icon_with_scale(
            frame_bgr, self._normalize_templates_to_bgr(), self.zoom
        )
        # 返回名称、模板信息与得分
        return best_name, best_img_info, best_score

    def _normalize_templates_to_bgr(self):
        """
        将传入的 icon_templates 统一转换为 BGR 图像，供公共匹配函数使用。
        """
        normalized = {}
        for name, icon_template in self.icon_templates.items():
            if icon_template is None:
                continue
            try:
                img = icon_template
                if len(img.shape) == 3:
                    if img.shape[2] == 4:
                        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    else:
                        img_bgr = img
                elif len(img.shape) == 2:
                    img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                else:
                    continue
                if img_bgr.size == 0:
                    continue
                normalized[name] = img_bgr
            except Exception as e:
                print(f"[DEBUG] 规范化模板 {name} 为 BGR 时出错: {e}", flush=True)
        return normalized

    def match_images(self):
        """
        主图像匹配流程。
        """
        screenshot = self.take_screenshot()
        try:
            # 使用新的彩色匹配逻辑，而不是旧的缩放匹配
            best_name, best_img_info, best_score = self._match_templates_on_frame(screenshot)

            # 先触发预览回调（如果有）：让 GUI 使用同一份截图与匹配结果进行展示
            if self.frame_callback is not None and screenshot is not None:
                try:
                    self.frame_callback(screenshot, best_img_info, best_name, best_score)
                except Exception as cb_err:
                    print(f"[DEBUG] 预览回调执行出错: {cb_err}", flush=True)

            # 再执行按键处理逻辑（只关心名称和得分）
            match_result = (best_name, best_score)
            self.handler_result(match_result)
        except Exception as e:
            print(f"匹配过程中出错: {e}", flush=True)


