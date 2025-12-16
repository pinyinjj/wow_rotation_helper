import cv2
import numpy as np


class TemplateMatcher:
    """
    公共的模板匹配 / HDR 处理封装：
    - 不依赖 GUI 或按键逻辑
    - 仅关注图像预处理与模板匹配算法

    供 `rotation.matcher.ImageMatcher` 和 `gui/uis/pages/capture_page.Ui_CapturePage`
    等模块共同调用，避免相互导入。
    """

    @staticmethod
    def apply_hdr_correction(frame_bgr, dark_factor: float = 0.3):
        """
        针对开启 HDR 时截图偏亮的问题，对截图做「色调映射」+ 额外整体压暗。

        参数：
        - frame_bgr: 输入的 BGR 图像
         - dark_factor: 进一步整体压暗系数，范围建议 0.1 ~ 5.0
        """
        try:
            # 转为 float32，范围 [0, 1]
            img_bgr = frame_bgr.astype(np.float32) / 255.0
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

            # 计算物理意义上的亮度（近似）
            r = img_rgb[..., 0]
            g = img_rgb[..., 1]
            b = img_rgb[..., 2]
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b  # [0, 1] 范围

            # Reinhard 风格的全局色调映射：只在高亮区域起明显作用
            luminance_mapped = luminance / (1.0 + luminance)

            # 计算缩放比例，保持颜色比例不变
            eps = 1e-6
            scale = luminance_mapped / (luminance + eps)
            scale = np.clip(scale, 0.0, 1.5)  # 防止极端值

            img_rgb_tm = img_rgb * scale[..., None]

            # 进一步整体压暗，避免 HDR 下仍然过亮
            img_rgb_tm = img_rgb_tm * float(dark_factor)
            img_rgb_tm = np.clip(img_rgb_tm, 0.0, 1.0)

            out_bgr = cv2.cvtColor((img_rgb_tm * 255.0).astype(np.uint8), cv2.COLOR_RGB2BGR)
            return out_bgr
        except Exception as e:
            print(f"[TemplateMatcher] HDR 亮度压缩失败，使用原始截图: {e}", flush=True)
            return frame_bgr

    @staticmethod
    def _validate_frame(frame_bgr):
        """验证帧是否有效"""
        if frame_bgr is None or getattr(frame_bgr, "size", 0) == 0:
            return None, None
        try:
            frame_h, frame_w = frame_bgr.shape[:2]
            return frame_h, frame_w
        except Exception as e:
            print(f"[TemplateMatcher] 读取截图尺寸失败: {e}", flush=True)
            return None, None
    
    @staticmethod
    def _validate_template(tmpl_bgr):
        """验证模板是否有效"""
        if tmpl_bgr is None or getattr(tmpl_bgr, "size", 0) == 0:
            return None, None
        h, w = tmpl_bgr.shape[:2]
        if h <= 0 or w <= 0:
            return None, None
        return h, w
    
    @staticmethod
    def _prepare_scaled_template(tmpl_bgr, scale, frame_h, frame_w):
        """准备缩放后的模板"""
        h, w = tmpl_bgr.shape[:2]
        
        if abs(scale - 1.0) > 1e-3:
            new_w = int(max(1, round(w * scale)))
            new_h = int(max(1, round(h * scale)))
            if new_h > frame_h or new_w > frame_w:
                return None, None, None
            use_bgr = cv2.resize(tmpl_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
            return use_bgr, new_w, new_h
        else:
            if h > frame_h or w > frame_w:
                return None, None, None
            return tmpl_bgr, w, h
    
    @staticmethod
    def _match_template(frame_bgr, template_bgr, name):
        """执行模板匹配"""
        try:
            res = cv2.matchTemplate(frame_bgr, template_bgr, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            return max_val, max_loc
        except Exception as e:
            print(f"[TemplateMatcher] 匹配 {name} 时出错: {e}", flush=True)
            return None, None
    
    @staticmethod
    def match_best_icon_with_scale(frame_bgr, templates_dict, scale: float):
        """
        公共匹配函数：**直接使用彩色 BGR 图像 + 缩放** 进行模板匹配。

        参数：
        - frame_bgr: 当前帧 BGR 图像
        - templates_dict: {name: tmpl_bgr} 字典
        - scale: 模板缩放倍率（0.1 - 5.0）

        返回：
        - best_name: 最佳匹配名称或 None
        - best_img_info: (tmpl_bgr_used, top_left, (w, h)) 或 None
        - best_score: 最佳匹配分数（float）
        """
        frame_h, frame_w = TemplateMatcher._validate_frame(frame_bgr)
        if frame_h is None:
            return None, None, None

        best_name = None
        best_img_info = None
        best_score = -1.0
        scale = max(0.1, min(5.0, float(scale)))

        for name, tmpl_bgr in templates_dict.items():
            h, w = TemplateMatcher._validate_template(tmpl_bgr)
            if h is None:
                continue

            use_bgr, use_w, use_h = TemplateMatcher._prepare_scaled_template(
                tmpl_bgr, scale, frame_h, frame_w
            )
            if use_bgr is None:
                continue

            max_val, max_loc = TemplateMatcher._match_template(frame_bgr, use_bgr, name)
            if max_val is None:
                continue

            if max_val > best_score:
                best_score = max_val
                best_name = name
                best_img_info = (use_bgr, max_loc, (use_w, use_h))

        return best_name, best_img_info, best_score


