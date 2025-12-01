"""
独立预览脚本（完全独立实现逻辑，不依赖主程序开关）

功能：
- 读取 `crop_config.json`，根据当前分辨率计算截取区域
- 从 `templates` 目录加载 `slice.png / defend.png / execute.png`
- 使用与主程序一致的模板匹配算法（TM_CCOEFF_NORMED）
- 左侧：当前截屏 + 匹配框与轻微叠加；右侧：各模板预览（带匹配区域）
- 不触发任何按键，仅用于“模板匹配程度预览”

退出方式：在 OpenCV 预览窗口中按下键盘 `q`。
"""

from __future__ import annotations

from typing import Optional, Tuple

import os
import json
import time

import mss
import cv2
import numpy as np


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "crop_config.json")


class PreviewState:
    """仅用于 preview.py 的轻量状态（和 main.py 无关）。"""

    def __init__(self) -> None:
        self.config: dict = {}
        self.template_cache: dict = {}


preview_state = PreviewState()


def apply_brightness_correction(bgr_image: np.ndarray) -> np.ndarray:
    """应用亮度修正（与主程序逻辑保持一致）。"""
    if bgr_image is None or bgr_image.size == 0:
        return bgr_image
    img = bgr_image.astype(np.float32) / 255.0
    settings = (preview_state.config.get("settings") or {}) if isinstance(preview_state.config, dict) else {}
    gain = float(settings.get("brightness_gain", 1.0))
    gamma = float(settings.get("brightness_gamma", 1.0))
    img *= gain
    img = np.power(np.clip(img, 0.0, 1.0), gamma)
    return (np.clip(img, 0.0, 1.0) * 255.0).astype(np.uint8)


def _load_match_templates() -> list:
    """从 templates 目录加载模板，返回 (文件名, BGR图, mask) 列表。"""
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    candidate_files = [
        os.path.join(templates_dir, "slice.png"),
        os.path.join(templates_dir, "defend.png"),
        os.path.join(templates_dir, "execute.png"),
    ]
    loaded = []
    for path in candidate_files:
        if os.path.exists(path):
            name = os.path.basename(path).lower()
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img is None or img.size == 0:
                continue
            # 构造 BGR 模板和全 255 的 mask（全部参与匹配）
            if img.ndim == 3 and img.shape[2] == 4:
                tmpl_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            elif img.ndim == 3:
                tmpl_bgr = img.copy()
            else:
                tmpl_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            h, w = tmpl_bgr.shape[:2]
            mask = np.full((h, w), 255, dtype=np.uint8)
            loaded.append((os.path.basename(path), tmpl_bgr, mask))
    return loaded


def _build_template_cache(loaded_templates: list) -> None:
    """
    构建/缓存模板的缩放版本及参数：
    - tmpl_bgr_resized: 缩放后的 BGR 模板（用于叠加）
    - tmpl_gray: 灰度模板（用于匹配）
    - mask: 缩放后的 mask
    - preview: 将背景设置为白色的灰度预览图
    - scale, threshold: 来自配置文件的参数
    """
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f) or {}
    except Exception:
        cfg = {}
    preview_state.config = cfg
    m_all = cfg.get("matching", {})

    for entry in loaded_templates:
        name, tmpl_bgr, tmpl_mask = entry
        nm = name.lower()
        if nm not in ("defend.png", "execute.png", "slice.png"):
            continue
        key = (
            "defend" if nm == "defend.png" else
            ("execute" if nm == "execute.png" else
             ("slice" if nm == "slice.png" else None))
        )
        m = m_all.get(key, {}) if key else {}
        default_scale = 0.53 if nm == "defend.png" else 1.0
        scale = float(m.get("scale", default_scale))
        threshold = float(m.get("threshold", 0.8))

        th, tw = tmpl_bgr.shape[:2]
        new_w = max(1, int(round(tw * max(scale, 1e-3))))
        new_h = max(1, int(round(th * max(scale, 1e-3))))

        resized_bgr = cv2.resize(tmpl_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
        resized_mask = cv2.resize(tmpl_mask, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
        tmpl_gray = cv2.cvtColor(resized_bgr, cv2.COLOR_BGR2GRAY)
        gray_preview = tmpl_gray.copy()
        if resized_mask is not None:
            gray_preview[resized_mask == 0] = 255

        preview_state.template_cache[name] = {
            "tmpl_bgr_resized": resized_bgr,
            "tmpl_gray": tmpl_gray,
            "mask": resized_mask,
            "preview": gray_preview,
            "scale": scale,
            "threshold": threshold,
        }


def _match_templates_on_frame(
    bgr_frame: np.ndarray,
    loaded_templates: list,
) -> Tuple[dict, Optional[dict], dict]:
    """
    在单帧上做模板匹配（与主程序算法一致，但去掉按键触发部分）。

    返回:
    - scaled_for_preview: dict[name -> 灰度模板预览图]
    - best_overlay: 全局最佳匹配的信息（可为 None）
    - per_template_best: dict[name -> 该模板的最佳匹配信息]
    """
    if not loaded_templates:
        return {}, None, {}

    frame_gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)

    scaled_for_preview: dict[str, np.ndarray] = {}
    best_score: float = 0.0
    best_name: Optional[str] = None
    best_overlay: Optional[dict] = None
    per_template_best: dict[str, dict] = {}

    for entry in loaded_templates:
        name, tmpl_bgr, tmpl_mask = entry
        nm = name.lower()
        if nm not in ("defend.png", "execute.png", "slice.png"):
            continue

        cache = preview_state.template_cache.get(name)
        if cache is None:
            _build_template_cache([entry])
            cache = preview_state.template_cache.get(name)
        if cache is None:
            continue

        work_tmpl_bgr = cache["tmpl_bgr_resized"]
        work_tmpl_gray = cache["tmpl_gray"]
        mask_resized = cache["mask"]
        local_threshold = float(cache.get("threshold", 0.8))

        h_t, w_t = work_tmpl_gray.shape[:2]
        scaled_for_preview[name] = cache["preview"]
        if h_t > frame_gray.shape[0] or w_t > frame_gray.shape[1]:
            continue

        res = cv2.matchTemplate(frame_gray, work_tmpl_gray, cv2.TM_CCOEFF_NORMED)
        _, maxVal, _, maxLoc = cv2.minMaxLoc(res)

        if maxVal > best_score:
            best_score = maxVal
            best_name = name
            best_overlay = {
                "name": name,
                "loc": maxLoc,
                "tmpl": work_tmpl_bgr,
                "mask": mask_resized,
                "score": maxVal,
                "threshold": local_threshold,
            }

        prev = per_template_best.get(name)
        if prev is None or maxVal > prev.get("score", 0.0):
            per_template_best[name] = {
                "name": name,
                "loc": maxLoc,
                "tmpl": work_tmpl_bgr,
                "mask": mask_resized,
                "score": maxVal,
                "threshold": local_threshold,
            }

    # best_overlay 现在仅用于调试，有需要可以在此处使用
    _ = best_name  # 占位，避免未使用变量告警

    return scaled_for_preview, best_overlay, per_template_best


def _compose_unified_preview(frame_bgr: np.ndarray, scaled: dict) -> np.ndarray:
    """合成左侧画面 + 右侧模板预览的总图像（与主程序一致）。"""
    if frame_bgr is None or frame_bgr.size == 0:
        return frame_bgr
    tiles: list[np.ndarray] = []
    for _, tmpl in scaled.items():
        if tmpl.ndim == 2:
            tile = cv2.cvtColor(tmpl, cv2.COLOR_GRAY2BGR)
        else:
            tile = tmpl
        tiles.append(tile)

    if not tiles:
        return frame_bgr

    max_w = max(t.shape[1] for t in tiles)
    total_h = sum(t.shape[0] for t in tiles)
    pad = 6
    total_h += pad * (len(tiles) - 1)

    right = np.full((total_h, max_w, 3), 255, dtype=np.uint8)
    y = 0
    for t in tiles:
        h, w = t.shape[:2]
        right[y:y + h, 0:w] = t
        y += h + pad

    h_left, w_left = frame_bgr.shape[:2]
    h_right, _ = right.shape[:2]
    H = max(h_left, h_right)

    def pad_to_h(img: np.ndarray, H: int) -> np.ndarray:
        if img.shape[0] == H:
            return img
        pad_h = H - img.shape[0]
        bottom = np.full((pad_h, img.shape[1], img.shape[2]), 255, dtype=img.dtype)
        return np.vstack([img, bottom])

    left_padded = pad_to_h(frame_bgr, H)
    right_padded = pad_to_h(right, H)
    sep = np.full((H, 4, 3), 255, dtype=np.uint8)
    combined = np.hstack([left_padded, sep, right_padded])
    return combined


def _overlay_per_template(frame_bgr: np.ndarray, per_template: dict) -> np.ndarray:
    """在图像上画出每个模板当前最佳匹配的矩形，并轻微叠加模板。"""
    if frame_bgr is None or frame_bgr.size == 0 or not per_template:
        return frame_bgr
    out = frame_bgr.copy()
    H, W = out.shape[:2]
    for _, data in per_template.items():
        x, y = data.get("loc", (0, 0))
        tmpl: np.ndarray = data.get("tmpl")
        mask: np.ndarray = data.get("mask")
        if tmpl is None or mask is None:
            continue
        h, w = tmpl.shape[:2]
        if x < 0 or y < 0 or x + w > W or y + h > H:
            continue
        score = data.get("score")
        thr = data.get("threshold", 0.7)
        color = (0, 0, 255) if (
            isinstance(score, (int, float))
            and isinstance(thr, (int, float))
            and score >= float(thr)
        ) else (0, 255, 0)
        cv2.rectangle(out, (x, y), (x + w, y + h), color, 2)
        roi = out[y:y + h, x:x + w]
        alpha = (mask.astype(np.float32) / 255.0)[..., None] * 0.3
        roi[:] = (roi.astype(np.float32) * (1.0 - alpha) + tmpl.astype(np.float32) * alpha).astype(np.uint8)
    return out


def _load_crop_config() -> Tuple[float, float, float, dict, callable, int]:
    """
    读取截取配置，返回：
    - size_frac, vertical_bias, height_frac
    - cfg: 完整配置
    - resolve_for: 用于根据分辨率计算参数的函数
    - fps: 匹配帧率
    """
    size_frac = 0.09
    vertical_bias = 0.11
    height_frac = 2

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f) or {}
    except Exception:
        # 配置缺失时使用默认值
        cfg = {}
        return size_frac, vertical_bias, height_frac, cfg, lambda w, h: (size_frac, vertical_bias, height_frac), 10

    preview_state.config = cfg
    settings = cfg.get("settings", {})
    fps = int(settings.get("fps", 10))

    res_map = cfg.get("resolutions", {})
    default = res_map.get("default", {})

    def resolve_for(mon_w: int, mon_h: int) -> Tuple[float, float, float]:
        key = f"{mon_w}x{mon_h}"
        res_cfg = res_map.get(key) or {}
        base = res_cfg if res_cfg else default
        params = (
            float(base.get("size_fraction", size_frac)),
            float(base.get("vertical_bias", vertical_bias)),
            float(base.get("height_fraction", height_frac)),
        )
        print(f"resolution: {mon_w}x{mon_h}")
        print(f"size_fraction: {params[0]}")
        print(f"vertical_bias: {params[1]}")
        print(f"height_fraction: {params[2]}")
        return params

    return size_frac, vertical_bias, height_frac, cfg, resolve_for, fps


def run_preview(duration_seconds: Optional[int] = None) -> None:
    """
    运行单独的预览窗口。

    参数
    - duration_seconds: 预览时长（秒）。若为 None，则持续运行直到按下 `q`。
    """
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        mon_left = int(monitor.get("left", 0))
        mon_top = int(monitor.get("top", 0))
        mon_w = int(monitor.get("width", 0))
        mon_h = int(monitor.get("height", 0))

        _, _, _, _, resolve_for, fps = _load_crop_config()
        size_f, vertical_b, height_f = resolve_for(mon_w, mon_h)
        side = int(max(1, min(mon_w, mon_h) * float(size_f)))
        crop_h = int(max(1, side * float(height_f)))
        center_x = mon_left + mon_w // 2
        center_y = mon_top + mon_h // 2 + int(mon_h * float(vertical_b))

        left = int(center_x - side // 2)
        top = int(center_y - crop_h // 2)
        left = max(mon_left, min(left, mon_left + mon_w - side))
        top = max(mon_top, min(top, mon_top + mon_h - crop_h))

        region = {"left": left, "top": top, "width": side, "height": crop_h}

        loaded_templates = _load_match_templates()
        _build_template_cache(loaded_templates)
        interval = 1.0 / max(1, fps)
        last_match_time = 0.0
        latest_scaled: dict = {}
        per_template: dict = {}

        print("🔍 仅预览模式已启动")
        print(" - 使用与主程序一致的模板与匹配算法")
        print(" - 不会触发任何按键，仅可视化匹配结果")
        print(" - 在预览窗口中按下键盘 `q` 以退出")

        start = time.time()
        while True:
            frame_bgra = sct.grab(region)
            frame = np.array(frame_bgra)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            frame = apply_brightness_correction(frame)

            loop_start = time.time()
            now = loop_start
            if loaded_templates and (now - last_match_time) >= interval:
                last_match_time = now
                latest_scaled, best_overlay, per_template = _match_templates_on_frame(frame, loaded_templates)
                _ = best_overlay  # 目前仅用于调试，占位

            frame_with_overlay = _overlay_per_template(frame, per_template)
            preview_img = _compose_unified_preview(frame_with_overlay, latest_scaled)
            cv2.imshow("Preview", preview_img)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            if duration_seconds is not None and (now - start) >= duration_seconds:
                break

            sleep_s = interval - (time.time() - loop_start)
            if sleep_s > 0:
                time.sleep(sleep_s)

        cv2.destroyAllWindows()


def main():
    """命令行入口：启动无限时长的预览（按 q 退出）。"""
    run_preview(duration_seconds=None)


if __name__ == "__main__":
    main()


