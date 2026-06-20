"""Exposure and brightness distribution analysis."""

from __future__ import annotations

import cv2
import numpy as np


def analyze_exposure(bgr: np.ndarray) -> dict:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    total = gray.size
    mean_val = float(gray.mean())

    dark_clip = float(np.sum(hist[:8]) / total)
    bright_clip = float(np.sum(hist[248:]) / total)

    # Ideal mean around 110-145 (slightly below mid-gray for natural photos)
    mean_score = 100 - min(100, abs(mean_val - 128) / 128 * 100)
    clip_penalty = (dark_clip + bright_clip) * 200
    score = max(0.0, min(100.0, mean_score * 0.6 + (100 - clip_penalty) * 0.4))

    if bright_clip > 0.05:
        label = "过曝"
    elif dark_clip > 0.05:
        label = "欠曝"
    elif mean_val < 90:
        label = "整体偏暗"
    elif mean_val > 170:
        label = "整体偏亮"
    else:
        label = "曝光正常"

    return {
        "score": round(score, 1),
        "mean_brightness": round(mean_val, 1),
        "dark_clip_ratio": round(dark_clip, 4),
        "bright_clip_ratio": round(bright_clip, 4),
        "label": label,
        "metric": "histogram_exposure",
    }
