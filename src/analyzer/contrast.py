"""Global contrast estimation (RMS contrast)."""

from __future__ import annotations

import cv2
import numpy as np


def analyze_contrast(bgr: np.ndarray) -> dict:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    mean = float(gray.mean())
    if mean < 1:
        rms = 0.0
    else:
        rms = float(np.sqrt(np.mean((gray - mean) ** 2)))

    # RMS contrast typical range ~20-80 for natural images
    if rms < 15:
        score = rms / 15 * 40
        label = "对比度偏低"
    elif rms < 30:
        score = 40 + (rms - 15) / 15 * 30
        label = "对比度一般"
    elif rms < 55:
        score = 70 + (rms - 30) / 25 * 20
        label = "对比度良好"
    else:
        score = min(100.0, 90 + (rms - 55) / 30 * 10)
        label = "对比度优秀"

    return {
        "score": round(score, 1),
        "rms_contrast": round(rms, 2),
        "label": label,
        "metric": "rms_contrast",
    }
