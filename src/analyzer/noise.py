"""Noise estimation using Immerkaer high-pass filter (1996)."""

from __future__ import annotations

import cv2
import numpy as np


def _immerkaer_sigma(gray: np.ndarray) -> float:
    """Fast noise sigma estimator; see Immerkaer, J. (1996)."""
    h, w = gray.shape
    if h < 4 or w < 4:
        return 0.0
    f = gray.astype(np.float64)
    kernel = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], dtype=np.float64)
    response = cv2.filter2D(f, -1, kernel)
    inner = response[1:-1, 1:-1]
    mad = float(np.mean(np.abs(inner)))
    return mad * np.sqrt(np.pi / 2.0) / 6.0


def analyze_noise(bgr: np.ndarray) -> dict:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    noise_level = _immerkaer_sigma(gray)

    # Empirical sigma thresholds on 8-bit grayscale
    if noise_level < 2.5:
        score = 95 + min(5, (2.5 - noise_level))
        label = "噪点极低"
    elif noise_level < 6:
        score = 75 + (6 - noise_level) / 3.5 * 20
        label = "噪点轻微"
    elif noise_level < 12:
        score = 50 + (12 - noise_level) / 6 * 25
        label = "噪点中等"
    elif noise_level < 22:
        score = 25 + (22 - noise_level) / 10 * 25
        label = "噪点明显"
    else:
        score = max(0.0, 25 - (noise_level - 22) / 18 * 25)
        label = "噪点严重"

    return {
        "score": round(min(100.0, score), 1),
        "noise_level": round(noise_level, 2),
        "label": label,
        "metric": "immerkaer_sigma",
    }
