"""Aggregate quality scoring and human-readable summaries."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Literal, Optional

import numpy as np

from .contrast import analyze_contrast
from .decoder import ImageInfo, decode_image
from .exposure import analyze_exposure
from .noise import analyze_noise
from .sharpness import analyze_sharpness

AnalysisMethod = Literal["traditional", "dl", "hybrid"]

WEIGHTS = {
    "sharpness": 0.35,
    "exposure": 0.25,
    "noise": 0.25,
    "contrast": 0.15,
}

HYBRID_TRADITIONAL_WEIGHT = 0.5
HYBRID_DL_WEIGHT = 0.5

METHOD_LABELS = {
    "traditional": "传统算法",
    "dl": "深度学习",
    "hybrid": "混合模式",
}


@dataclass
class DimensionResult:
    name: str
    name_cn: str
    score: float
    label: str
    details: dict = field(default_factory=dict)


@dataclass
class QualityReport:
    overall_score: float
    grade: str
    summary: str
    dimensions: list[DimensionResult]
    image_info: ImageInfo
    elapsed_ms: float
    analysis_edge: int
    method: str = "traditional"
    dl_score: Optional[float] = None
    traditional_score: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "grade": self.grade,
            "summary": self.summary,
            "elapsed_ms": self.elapsed_ms,
            "method": self.method,
            "dl_score": self.dl_score,
            "traditional_score": self.traditional_score,
            "dimensions": [
                {
                    "name": d.name,
                    "name_cn": d.name_cn,
                    "score": d.score,
                    "label": d.label,
                    "details": d.details,
                }
                for d in self.dimensions
            ],
            "image_info": {
                "format": self.image_info.format_name,
                "width": self.image_info.width,
                "height": self.image_info.height,
                "megapixels": self.image_info.megapixels,
                "file_size_kb": self.image_info.file_size_kb,
            },
        }


def _grade(score: float) -> str:
    if score >= 90:
        return "A 优秀"
    if score >= 75:
        return "B 良好"
    if score >= 60:
        return "C 一般"
    if score >= 40:
        return "D 较差"
    return "E 很差"


def _build_summary(dims: list[DimensionResult]) -> str:
    parts = [f"{d.name_cn}：{d.label}" for d in dims]
    return "；".join(parts) + "。"


def _adjust_sharpness_for_noise(sharp: dict, noise: dict) -> tuple[float, str, bool]:
    """
    Laplacian 对噪点敏感：高噪 + 高方差时下调清晰度分，避免颗粒被误判为细节。
    返回 (校正后分数, 标签, 是否触发校正)。
    """
    score = float(sharp["score"])
    label = sharp["label"]
    nl = float(noise.get("noise_level", 0))
    variance = float(sharp.get("variance", 0))

    if nl > 6 and variance > 120:
        excess = min(1.0, (nl - 6) / 18)
        adjusted = score * (1 - 0.75 * excess) + noise["score"] * 0.2 * excess
        score = max(0.0, min(100.0, adjusted))
        if excess > 0.4:
            label = f"{label}（噪点干扰已校正）"
        return round(score, 1), label, True
    return score, label, False


def _traditional_dimensions(bgr: np.ndarray) -> tuple[list[DimensionResult], float]:
    sharp = analyze_sharpness(bgr)
    expo = analyze_exposure(bgr)
    noise = analyze_noise(bgr)
    contrast = analyze_contrast(bgr)

    sharp_score, sharp_label, sharp_adjusted = _adjust_sharpness_for_noise(sharp, noise)
    sharp_details = {**sharp, "adjusted_score": sharp_score, "noise_corrected": sharp_adjusted}

    dims = [
        DimensionResult("sharpness", "清晰度", sharp_score, sharp_label, sharp_details),
        DimensionResult("exposure", "曝光", expo["score"], expo["label"], expo),
        DimensionResult("noise", "噪点", noise["score"], noise["label"], noise),
        DimensionResult("contrast", "对比度", contrast["score"], contrast["label"], contrast),
    ]
    overall = sum(d.score * WEIGHTS[d.name] for d in dims)
    return dims, overall


def _dl_dimension(bgr: np.ndarray) -> tuple[DimensionResult, float]:
    from .dl_scorer import analyze_dl_quality

    dl = analyze_dl_quality(bgr)
    dim = DimensionResult("deep_learning", "深度学习画质", dl["score"], dl["label"], dl)
    return dim, dl["score"]


def _compose_report(
    *,
    dims: list[DimensionResult],
    overall: float,
    info: ImageInfo,
    elapsed_ms: float,
    analysis_edge: int,
    method: AnalysisMethod,
    dl_score: Optional[float] = None,
    traditional_score: Optional[float] = None,
) -> QualityReport:
    return QualityReport(
        overall_score=round(overall, 1),
        grade=_grade(overall),
        summary=_build_summary(dims),
        dimensions=dims,
        image_info=info,
        elapsed_ms=round(elapsed_ms, 1),
        analysis_edge=analysis_edge,
        method=method,
        dl_score=dl_score,
        traditional_score=traditional_score,
    )


def analyze_image(
    source: str | bytes,
    *,
    analysis_max_edge: int = 1280,
    method: AnalysisMethod = "traditional",
) -> QualityReport:
    start = time.perf_counter()
    bgr, info = decode_image(source, for_analysis=True, max_edge=analysis_max_edge)

    if method == "traditional":
        dims, overall = _traditional_dimensions(bgr)
        dl_score = None
        traditional_score = overall
    elif method == "dl":
        dl_dim, dl_score = _dl_dimension(bgr)
        dims = [dl_dim]
        overall = dl_score
        traditional_score = None
    elif method == "hybrid":
        trad_dims, traditional_score = _traditional_dimensions(bgr)
        dl_dim, dl_score = _dl_dimension(bgr)
        dims = [*trad_dims, dl_dim]
        overall = traditional_score * HYBRID_TRADITIONAL_WEIGHT + dl_score * HYBRID_DL_WEIGHT
    else:
        raise ValueError(f"未知评分模式: {method!r}")

    elapsed_ms = (time.perf_counter() - start) * 1000
    return _compose_report(
        dims=dims,
        overall=overall,
        info=info,
        elapsed_ms=elapsed_ms,
        analysis_edge=analysis_max_edge,
        method=method,
        dl_score=dl_score,
        traditional_score=traditional_score,
    )


def analyze_ndarray(
    bgr: np.ndarray,
    info: Optional[ImageInfo] = None,
    *,
    method: AnalysisMethod = "traditional",
) -> QualityReport:
    """Analyze an already-decoded BGR image (for tests)."""
    start = time.perf_counter()

    if method == "traditional":
        dims, overall = _traditional_dimensions(bgr)
        dl_score = None
        traditional_score = overall
    elif method == "dl":
        dl_dim, dl_score = _dl_dimension(bgr)
        dims = [dl_dim]
        overall = dl_score
        traditional_score = None
    elif method == "hybrid":
        trad_dims, traditional_score = _traditional_dimensions(bgr)
        dl_dim, dl_score = _dl_dimension(bgr)
        dims = [*trad_dims, dl_dim]
        overall = traditional_score * HYBRID_TRADITIONAL_WEIGHT + dl_score * HYBRID_DL_WEIGHT
    else:
        raise ValueError(f"未知评分模式: {method!r}")

    elapsed_ms = (time.perf_counter() - start) * 1000

    if info is None:
        h, w = bgr.shape[:2]
        info = ImageInfo(
            path="array",
            format_name="N/A",
            width=w,
            height=h,
            megapixels=round(w * h / 1_000_000, 2),
            file_size_kb=0,
            has_alpha=False,
            decode_note="",
        )

    return _compose_report(
        dims=dims,
        overall=overall,
        info=info,
        elapsed_ms=elapsed_ms,
        analysis_edge=max(bgr.shape[:2]),
        method=method,
        dl_score=dl_score,
        traditional_score=traditional_score,
    )
