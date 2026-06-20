"""Generate synthetic test samples for quality analysis validation."""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "test_samples"


def _base_texture(w: int = 1600, h: int = 1200) -> np.ndarray:
    rng = np.random.default_rng(42)
    x = np.linspace(0, 8 * np.pi, w)
    y = np.linspace(0, 8 * np.pi, h)
    xv, yv = np.meshgrid(x, y)
    pattern = (np.sin(xv) * np.cos(yv) * 60 + 128).astype(np.float32)
    # High-frequency checkerboard helps Laplacian distinguish blur levels
    checker = ((np.arange(w) // 6 + np.arange(h)[:, None] // 6) % 2).astype(np.float32) * 22
    noise = rng.normal(0, 2.5, (h, w)).astype(np.float32)
    gray = np.clip(pattern + checker + noise, 0, 255).astype(np.uint8)
    bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    # Add color gradients for contrast
    bgr[:, :, 0] = np.clip(bgr[:, :, 0].astype(np.int16) + 10, 0, 255).astype(np.uint8)
    bgr[:, :, 2] = np.clip(bgr[:, :, 2].astype(np.int16) - 10, 0, 255).astype(np.uint8)
    return bgr


def generate_all() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {}

    base = _base_texture()
    categories = {}

    # Clear (2)
    clear_dir = OUT / "clear"
    clear_dir.mkdir(exist_ok=True)
    for old in clear_dir.glob("*.jpg"):
        old.unlink()
    for i in range(2):
        img = base.copy()
        path = clear_dir / f"clear_{i + 1}.jpg"
        cv2.imwrite(str(path), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        categories.setdefault("clear", []).append(str(path.relative_to(ROOT)))

    # Blur (3)
    blur_dir = OUT / "blur"
    blur_dir.mkdir(exist_ok=True)
    for old in blur_dir.glob("*.jpg"):
        old.unlink()
    kernels = [5, 15, 31]
    for i, k in enumerate(kernels):
        img = cv2.GaussianBlur(base, (k, k), 0)
        path = blur_dir / f"blur_k{k}.jpg"
        cv2.imwrite(str(path), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        categories.setdefault("blur", []).append(str(path.relative_to(ROOT)))

    # Overexpose (2)
    over_dir = OUT / "overexpose"
    over_dir.mkdir(exist_ok=True)
    for old in over_dir.glob("*.jpg"):
        old.unlink()
    for i, gain in enumerate([1.6, 2.0]):
        img = np.clip(base.astype(np.float32) * gain, 0, 255).astype(np.uint8)
        path = over_dir / f"over_{i + 1}.jpg"
        cv2.imwrite(str(path), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        categories.setdefault("overexpose", []).append(str(path.relative_to(ROOT)))

    # Underexpose (2)
    under_dir = OUT / "underexpose"
    under_dir.mkdir(exist_ok=True)
    for old in under_dir.glob("*.jpg"):
        old.unlink()
    for i, gain in enumerate([0.35, 0.5]):
        img = (base.astype(np.float32) * gain).astype(np.uint8)
        path = under_dir / f"under_{i + 1}.jpg"
        cv2.imwrite(str(path), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        categories.setdefault("underexpose", []).append(str(path.relative_to(ROOT)))

    # Noise (3)
    noise_dir = OUT / "noise"
    noise_dir.mkdir(exist_ok=True)
    for old in noise_dir.glob("*.jpg"):
        old.unlink()
    rng = np.random.default_rng(7)
    for i, sigma in enumerate([15, 30, 50]):
        noisy = base.astype(np.float32) + rng.normal(0, sigma, base.shape)
        img = np.clip(noisy, 0, 255).astype(np.uint8)
        path = noise_dir / f"noise_s{sigma}.jpg"
        cv2.imwrite(str(path), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        categories.setdefault("noise", []).append(str(path.relative_to(ROOT)))

    # Large image (12MP+) for performance test
    large_dir = OUT / "large"
    large_dir.mkdir(exist_ok=True)
    large = _base_texture(4000, 3000)  # 12 MP
    large_path = large_dir / "large_12mp.jpg"
    cv2.imwrite(str(large_path), large, [cv2.IMWRITE_JPEG_QUALITY, 92])
    categories["large"] = [str(large_path.relative_to(ROOT))]

    # Counterexample: fine grain noise inflates Laplacian — "sharp" score but poor quality
    counter_dir = OUT / "counterexample"
    counter_dir.mkdir(exist_ok=True)
    for old in counter_dir.glob("*.jpg"):
        old.unlink()
    rng2 = np.random.default_rng(99)
    grain = base.astype(np.float32) + rng2.normal(0, 38, base.shape)
    grain = np.clip(grain, 0, 255).astype(np.uint8)
    counter_path = counter_dir / "noise_masquerade_sharp.jpg"
    cv2.imwrite(str(counter_path), grain, [cv2.IMWRITE_JPEG_QUALITY, 75])
    categories["counterexample"] = [str(counter_path.relative_to(ROOT))]

    # Multi-format samples from same base
    fmt_dir = OUT / "formats"
    fmt_dir.mkdir(exist_ok=True)
    cv2.imwrite(str(fmt_dir / "sample.png"), base)
    cv2.imwrite(str(fmt_dir / "sample.webp"), base)
    cv2.imwrite(str(fmt_dir / "sample.jpg"), base, [cv2.IMWRITE_JPEG_QUALITY, 90])
    fmt_files = [
        str((fmt_dir / "sample.png").relative_to(ROOT)),
        str((fmt_dir / "sample.webp").relative_to(ROOT)),
        str((fmt_dir / "sample.jpg").relative_to(ROOT)),
    ]
    try:
        import pillow_heif
        from PIL import Image

        pillow_heif.register_heif_opener()
        rgb = cv2.cvtColor(base, cv2.COLOR_BGR2RGB)
        Image.fromarray(rgb).save(str(fmt_dir / "sample.heic"), format="HEIF")
        fmt_files.append(str((fmt_dir / "sample.heic").relative_to(ROOT)))
    except Exception as exc:
        print(f"HEIC sample skipped: {exc}")
    categories["formats"] = fmt_files

    meta["categories"] = categories
    meta["human_labels"] = {
        "clear": "人工：清晰、曝光正常、低噪",
        "blur": "人工：不同程度模糊，越大的 kernel 越模糊",
        "overexpose": "人工：过曝/高光溢出",
        "underexpose": "人工：欠曝/偏暗",
        "noise": "人工：噪点随 sigma 递增",
        "counterexample": "人工：颗粒噪点重，主观画质差，但 Laplacian 可能虚高",
    }

    (OUT / "manifest.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta


if __name__ == "__main__":
    result = generate_all()
    print(f"Generated samples under {OUT}")
    for cat, files in result["categories"].items():
        print(f"  {cat}: {len(files)} files")
