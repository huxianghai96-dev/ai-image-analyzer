"""Multi-format image decoder with memory-safe loading for large images."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
ANALYSIS_MAX_EDGE = 1280
PREVIEW_MAX_EDGE = 1920


@dataclass
class ImageInfo:
    path: str
    format_name: str
    width: int
    height: int
    megapixels: float
    file_size_kb: float
    has_alpha: bool
    decode_note: str


def _register_heif() -> bool:
    try:
        import pillow_heif

        pillow_heif.register_heif_opener()
        return True
    except ImportError:
        return False


def _detect_format(path: Path, raw: bytes) -> str:
    ext = path.suffix.lower()
    if ext in SUPPORTED_EXTENSIONS:
        return ext.lstrip(".")
    if raw[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "webp"
    if raw[4:8] == b"ftyp":
        brand = raw[8:12]
        if brand in (b"heic", b"heix", b"hevc", b"mif1"):
            return "heic"
    return "unknown"


def _pil_to_bgr(image: Image.Image) -> np.ndarray:
    if image.mode in ("RGBA", "LA"):
        rgba = np.array(image.convert("RGBA"))
        bgr = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
        return bgr
    if image.mode != "RGB":
        image = image.convert("RGB")
    rgb = np.array(image)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def _resize_if_needed(image: np.ndarray, max_edge: int) -> np.ndarray:
    h, w = image.shape[:2]
    longest = max(h, w)
    if longest <= max_edge:
        return image
    scale = max_edge / longest
    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)


def decode_image(
    source: str | bytes,
    *,
    for_analysis: bool = True,
    max_edge: Optional[int] = None,
) -> Tuple[np.ndarray, ImageInfo]:
    """
    Decode JPEG/PNG/WebP/HEIC into BGR ndarray.

    Large images are downscaled before analysis to avoid OOM and keep latency low.
    """
    heif_ok = _register_heif()

    if isinstance(source, bytes):
        raw = source
        path = Path("memory")
    else:
        path = Path(source)
        raw = path.read_bytes()

    fmt = _detect_format(path, raw)
    edge = max_edge or (ANALYSIS_MAX_EDGE if for_analysis else PREVIEW_MAX_EDGE)

    decode_note = ""
    has_alpha = False

    if fmt in ("heic", "heif"):
        if not heif_ok:
            raise ValueError("HEIC 解码需要 pillow-heif，请运行: pip install pillow-heif")
        pil_img = Image.open(io.BytesIO(raw))
        has_alpha = pil_img.mode in ("RGBA", "LA")
        decode_note = "HEIC 为容器格式，解码后统一转为 BGR；部分设备需额外编解码库。"
        bgr = _pil_to_bgr(pil_img)
    elif fmt == "webp":
        # OpenCV handles animated WebP as first frame; PIL is more predictable for alpha.
        try:
            bgr = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
            if bgr is None:
                raise ValueError("OpenCV decode failed")
        except Exception:
            pil_img = Image.open(io.BytesIO(raw))
            has_alpha = pil_img.mode in ("RGBA", "LA")
            bgr = _pil_to_bgr(pil_img)
        decode_note = "WebP 支持有损/无损；含透明通道时会丢弃 Alpha 再分析。"
    elif fmt == "png":
        decoded = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_UNCHANGED)
        if decoded is None:
            raise ValueError("PNG 解码失败")
        if decoded.ndim == 3 and decoded.shape[2] == 4:
            has_alpha = True
            bgr = cv2.cvtColor(decoded, cv2.COLOR_BGRA2BGR)
        else:
            bgr = decoded if decoded.ndim == 3 else cv2.cvtColor(decoded, cv2.COLOR_GRAY2BGR)
        decode_note = "PNG 为无损格式；带 Alpha 通道时分析使用 RGB 部分。"
    elif fmt in ("jpeg", "jpg"):
        bgr = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("JPEG 解码失败")
        decode_note = "JPEG 为有损压缩；高压缩率会引入块效应，可能影响清晰度/噪点评分。"
    else:
        raise ValueError(f"不支持的格式: {fmt}")

    original_h, original_w = bgr.shape[:2]
    working = _resize_if_needed(bgr, edge)
    resized = working.shape[:2] != (original_h, original_w)

    if resized and for_analysis:
        decode_note += f" 分析前已缩放至最长边 {edge}px 以控制内存与耗时。"

    info = ImageInfo(
        path=str(path),
        format_name=fmt.upper(),
        width=original_w,
        height=original_h,
        megapixels=round(original_w * original_h / 1_000_000, 2),
        file_size_kb=round(len(raw) / 1024, 1),
        has_alpha=has_alpha,
        decode_note=decode_note.strip(),
    )
    return working, info


def format_comparison_text() -> str:
    return (
        "JPEG: 有损、体积小，适合照片；块效应与锐化会干扰 Laplacian 清晰度估计。\n"
        "PNG: 无损、可含透明；文件较大，噪点/压缩伪影较少。\n"
        "WebP: 有损/无损均可；移动端常见，解码需注意首帧与 Alpha。\n"
        "HEIC: 高效有损（Apple 默认）；需 pillow-heif，解码成本高于 JPEG。"
    )
