"""Sharpness estimation via Laplacian variance."""

from __future__ import annotations

import cv2
import numpy as np


def analyze_sharpness(bgr: np.ndarray) -> dict:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F, ksize=3)
    variance = float(lap.var())

    # Empirical mapping from Laplacian variance to 0-100 score.
    # Reference: Pech-Pacheco et al., "Diagnosis of Blur in Digital Images"
    if variance < 50:
        score = max(0.0, variance / 50 * 30)
        label = "严重模糊"
    elif variance < 150:
        score = 30 + (variance - 50) / 100 * 30
        label = "明显模糊"
    elif variance < 400:
        score = 60 + (variance - 150) / 250 * 15
        label = "轻度模糊"
    elif variance < 1000:
        score = 75 + (variance - 400) / 600 * 10
        label = "基本清晰"
    elif variance < 2500:
        score = 85 + (variance - 1000) / 1500 * 10
        label = "清晰"
    else:
        score = min(100.0, 95 + (variance - 2500) / 3000 * 5)
        label = "非常清晰"

    return {
        "score": round(score, 1),
        "variance": round(variance, 2),
        "label": label,
        "metric": "laplacian_variance",
    }
