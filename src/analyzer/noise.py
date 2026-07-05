"""Noise estimation using Immerkaer high-pass filter (1996)."""

from __future__ import annotations

import cv2
import numpy as np


def _robust_noise_sigma(gray: np.ndarray) -> float:
    """Robust noise sigma estimator combining high-pass and local variance."""
    h, w = gray.shape
    if h < 4 or w < 4:
        return 0.0
        
    f = gray.astype(np.float64)
    
    # 1. Immerkaer high-pass (good for fine, pixel-level Gaussian noise)
    kernel = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], dtype=np.float64)
    response = cv2.filter2D(f, -1, kernel)
    inner = response[1:-1, 1:-1]
    imm_sigma = float(np.mean(np.abs(inner))) * np.sqrt(np.pi / 2.0) / 6.0
    
    # 2. Median of local 5x5 variance (good for structured, mid-frequency smartphone noise)
    mean = cv2.blur(f, (5, 5))
    mean_sq = cv2.blur(f**2, (5, 5))
    var = mean_sq - mean**2
    median_std = float(np.sqrt(np.maximum(0, np.median(var))))
    
    # Return the maximum of both to capture both types of noise
    return max(imm_sigma, median_std)


def analyze_noise(bgr: np.ndarray) -> dict:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    abs_noise = _robust_noise_sigma(gray)
    
    # SNR adjustment: noise in dark images is visually much worse.
    # Cap minimum mean brightness to 10 to avoid division by zero.
    mean_brightness = max(10.0, float(np.mean(gray)))
    
    # Scale absolute noise to a reference brightness of 100.
    # If image is dark (e.g. mean=20), abs_noise is multiplied by 5.
    noise_level = abs_noise * (100.0 / mean_brightness)

    # Empirical thresholds based on the relative noise level
    if noise_level < 1.5:
        score = 95 + min(5.0, (1.5 - noise_level) * 3.3)
        label = "噪点极低"
    elif noise_level < 4.0:
        score = 80 + (4.0 - noise_level) / 2.5 * 15
        label = "噪点轻微"
    elif noise_level < 9.0:
        score = 60 + (9.0 - noise_level) / 5.0 * 20
        label = "噪点中等"
    elif noise_level < 18.0:
        score = 30 + (18.0 - noise_level) / 9.0 * 30
        label = "噪点明显"
    else:
        score = max(0.0, 30 - (noise_level - 18.0) / 15.0 * 30)
        label = "噪点严重"

    return {
        "score": round(min(100.0, score), 1),
        "noise_level": round(noise_level, 2),
        "abs_noise": round(abs_noise, 2),
        "label": label,
        "metric": "relative_immerkaer_sigma",
    }
