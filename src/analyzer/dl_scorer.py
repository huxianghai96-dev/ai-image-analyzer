"""Deep learning no-reference image quality assessment via pyiqa."""

from __future__ import annotations

import os
from typing import Any, Optional

import cv2
import numpy as np

# cnniqa is lighter than MANIQA/MUSIQ — better suited for mobile CPU inference.
DEFAULT_DL_MODEL = os.environ.get("IQA_DL_MODEL", "cnniqa")

_metric_name: Optional[str] = None
_metric: Any = None


class DLScorerUnavailableError(RuntimeError):
    """Raised when pyiqa/torch is not installed or model loading fails."""


def _dl_label(score: float) -> str:
    if score >= 85:
        return "画质优秀"
    if score >= 70:
        return "画质良好"
    if score >= 55:
        return "画质一般"
    if score >= 40:
        return "画质偏差"
    return "画质较差"


def _normalize_score(raw: float) -> float:
    """Map model output to 0–100 (pyiqa NR-IQA: higher is better)."""
    if 0.0 <= raw <= 1.0:
        return round(max(0.0, min(100.0, raw * 100.0)), 1)
    if 0.0 <= raw <= 100.0:
        return round(max(0.0, min(100.0, raw)), 1)
    return round(max(0.0, min(100.0, raw)), 1)


def get_dl_metric(model_name: str | None = None):
    """Lazy singleton loader for pyiqa metric (reloads only when model name changes)."""
    global _metric, _metric_name

    name = model_name or DEFAULT_DL_MODEL
    if _metric is not None and _metric_name == name:
        return _metric, name

    try:
        import pyiqa
        import torch
    except ImportError as exc:
        raise DLScorerUnavailableError(
            "未安装深度学习依赖。请执行：pip install -r requirements-dl.txt"
        ) from exc

    device = torch.device("cpu")
    try:
        metric = pyiqa.create_metric(name, device=device, as_loss=False)
        metric.eval()
    except Exception as exc:
        raise DLScorerUnavailableError(f"加载模型 {name!r} 失败：{exc}") from exc

    _metric = metric
    _metric_name = name
    return _metric, name


def _bgr_to_tensor(bgr: np.ndarray):
    import torch

    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return torch.from_numpy(rgb).float().permute(2, 0, 1).unsqueeze(0) / 255.0


def analyze_dl_quality(bgr: np.ndarray, *, model_name: str | None = None) -> dict:
    """Run NR-IQA on a BGR image; returns a 0–100 score and metadata."""
    import torch

    metric, name = get_dl_metric(model_name)
    tensor = _bgr_to_tensor(bgr)

    with torch.no_grad():
        raw = float(metric(tensor).item())

    score = _normalize_score(raw)
    return {
        "score": score,
        "label": _dl_label(score),
        "raw_output": raw,
        "model": name,
        "device": "cpu",
    }


def is_dl_available() -> bool:
    try:
        import pyiqa  # noqa: F401
        import torch  # noqa: F401

        return True
    except ImportError:
        return False
