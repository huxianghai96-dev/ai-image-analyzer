"""Generate synthetic test samples for quality analysis validation."""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "test_samples"


def _base_texture(w: int = 1600, h: int = 1200) -> np.ndarray:
    """Create a richer base texture mixing gradients, sine patterns, checkerboard, and soft noise."""
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


def _scene_texture(w: int = 1600, h: int = 1200, seed: int = 100) -> np.ndarray:
    """Create a more photo-like synthetic scene with sky gradient, ground, and random circles/rects."""
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), dtype=np.uint8)

    # Sky gradient (top half: blue → cyan)
    for row in range(h // 2):
        ratio = row / (h // 2)
        b = int(200 - ratio * 60)
        g = int(140 + ratio * 60)
        r = int(80 + ratio * 40)
        img[row, :] = [b, g, r]

    # Ground gradient (bottom half: green-brown)
    for row in range(h // 2, h):
        ratio = (row - h // 2) / (h // 2)
        b = int(40 + ratio * 20)
        g = int(120 - ratio * 50)
        r = int(80 + ratio * 30)
        img[row, :] = [b, g, r]

    # Random circles to simulate objects
    for _ in range(15):
        cx = rng.integers(50, w - 50)
        cy = rng.integers(50, h - 50)
        radius = int(rng.integers(20, 80))
        color = tuple(int(c) for c in rng.integers(40, 220, size=3))
        cv2.circle(img, (cx, cy), radius, color, -1, cv2.LINE_AA)

    # Add fine texture (slight Gaussian noise for realism)
    texture_noise = rng.normal(0, 4, img.shape).astype(np.float32)
    img = np.clip(img.astype(np.float32) + texture_noise, 0, 255).astype(np.uint8)

    return img


def generate_all() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {}

    base = _base_texture()
    scene = _scene_texture()
    categories = {}

    # ── Clear (3 samples) ─────────────────────────────────────────────────────
    clear_dir = OUT / "clear"
    clear_dir.mkdir(exist_ok=True)
    for old in clear_dir.glob("*.*"):
        old.unlink()

    # Sample 1: base texture (sharp, well-exposed)
    cv2.imwrite(str(clear_dir / "clear_texture.jpg"), base, [cv2.IMWRITE_JPEG_QUALITY, 95])
    categories.setdefault("clear", []).append(str((clear_dir / "clear_texture.jpg").relative_to(ROOT)))

    # Sample 2: scene-like image (sharp)
    cv2.imwrite(str(clear_dir / "clear_scene.jpg"), scene, [cv2.IMWRITE_JPEG_QUALITY, 95])
    categories.setdefault("clear", []).append(str((clear_dir / "clear_scene.jpg").relative_to(ROOT)))

    # Sample 3: mildly sharpened scene, kept below the over-sharpened counterexample level.
    scene_blur = cv2.GaussianBlur(scene, (0, 0), 1.2)
    sharpened = cv2.addWeighted(scene, 1.25, scene_blur, -0.25, 0)
    cv2.imwrite(str(clear_dir / "clear_sharp.jpg"), sharpened, [cv2.IMWRITE_JPEG_QUALITY, 95])
    categories.setdefault("clear", []).append(str((clear_dir / "clear_sharp.jpg").relative_to(ROOT)))

    # ── Blur (3 samples with increasing blur) ─────────────────────────────────
    blur_dir = OUT / "blur"
    blur_dir.mkdir(exist_ok=True)
    for old in blur_dir.glob("*.*"):
        old.unlink()
    kernels = [5, 15, 31]
    for k in kernels:
        img = cv2.GaussianBlur(scene, (k, k), 0)
        path = blur_dir / f"blur_k{k}.jpg"
        cv2.imwrite(str(path), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        categories.setdefault("blur", []).append(str(path.relative_to(ROOT)))

    # ── Overexpose (3 samples) ────────────────────────────────────────────────
    over_dir = OUT / "overexpose"
    over_dir.mkdir(exist_ok=True)
    for old in over_dir.glob("*.*"):
        old.unlink()
    for i, gain in enumerate([1.4, 1.8, 2.2]):
        img = np.clip(scene.astype(np.float32) * gain, 0, 255).astype(np.uint8)
        path = over_dir / f"over_{i + 1}_g{gain}.jpg"
        cv2.imwrite(str(path), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        categories.setdefault("overexpose", []).append(str(path.relative_to(ROOT)))

    # ── Underexpose (3 samples) ───────────────────────────────────────────────
    under_dir = OUT / "underexpose"
    under_dir.mkdir(exist_ok=True)
    for old in under_dir.glob("*.*"):
        old.unlink()
    for i, gain in enumerate([0.25, 0.4, 0.55]):
        img = (scene.astype(np.float32) * gain).astype(np.uint8)
        path = under_dir / f"under_{i + 1}_g{gain}.jpg"
        cv2.imwrite(str(path), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        categories.setdefault("underexpose", []).append(str(path.relative_to(ROOT)))

    # ── Noise (3 samples with increasing sigma) ───────────────────────────────
    noise_dir = OUT / "noise"
    noise_dir.mkdir(exist_ok=True)
    for old in noise_dir.glob("*.*"):
        old.unlink()
    rng = np.random.default_rng(7)
    for sigma in [15, 30, 50]:
        noisy = scene.astype(np.float32) + rng.normal(0, sigma, scene.shape)
        img = np.clip(noisy, 0, 255).astype(np.uint8)
        path = noise_dir / f"noise_s{sigma}.jpg"
        cv2.imwrite(str(path), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        categories.setdefault("noise", []).append(str(path.relative_to(ROOT)))

    # ── Large image (12MP+) for performance test ──────────────────────────────
    large_dir = OUT / "large"
    large_dir.mkdir(exist_ok=True)
    large = _scene_texture(4000, 3000, seed=200)  # 12 MP
    large_path = large_dir / "large_12mp.jpg"
    cv2.imwrite(str(large_path), large, [cv2.IMWRITE_JPEG_QUALITY, 92])
    categories["large"] = [str(large_path.relative_to(ROOT))]

    # ── Counterexamples (3 failure modes) ─────────────────────────────────────
    counter_dir = OUT / "counterexample"
    counter_dir.mkdir(exist_ok=True)
    for old in counter_dir.glob("*.*"):
        old.unlink()

    # CE1: Fine grain noise inflates Laplacian — "sharp" score but poor quality
    rng2 = np.random.default_rng(99)
    grain = base.astype(np.float32) + rng2.normal(0, 38, base.shape)
    grain = np.clip(grain, 0, 255).astype(np.uint8)
    counter1 = counter_dir / "noise_masquerade_sharp.jpg"
    cv2.imwrite(str(counter1), grain, [cv2.IMWRITE_JPEG_QUALITY, 75])
    categories.setdefault("counterexample", []).append(str(counter1.relative_to(ROOT)))

    # CE2: Over-sharpened (USM halo) — Laplacian very high but visual artifacts
    over_sharp = cv2.GaussianBlur(scene, (0, 0), 3)
    over_sharp = cv2.addWeighted(scene, 2.5, over_sharp, -1.5, 0)
    counter2 = counter_dir / "over_sharpened_halo.jpg"
    cv2.imwrite(str(counter2), over_sharp, [cv2.IMWRITE_JPEG_QUALITY, 85])
    categories.setdefault("counterexample", []).append(str(counter2.relative_to(ROOT)))

    # CE3: Low-contrast foggy scene — appears bright but washed out
    foggy = scene.astype(np.float32) * 0.35 + 160
    foggy = np.clip(foggy, 0, 255).astype(np.uint8)
    counter3 = counter_dir / "foggy_low_contrast.jpg"
    cv2.imwrite(str(counter3), foggy, [cv2.IMWRITE_JPEG_QUALITY, 90])
    categories.setdefault("counterexample", []).append(str(counter3.relative_to(ROOT)))

    # ── Multi-format samples from same base ───────────────────────────────────
    fmt_dir = OUT / "formats"
    fmt_dir.mkdir(exist_ok=True)
    for old in fmt_dir.glob("*.*"):
        if old.name != "manifest.json":
            old.unlink()
    cv2.imwrite(str(fmt_dir / "sample.png"), scene)
    cv2.imwrite(str(fmt_dir / "sample.webp"), scene)
    cv2.imwrite(str(fmt_dir / "sample.jpg"), scene, [cv2.IMWRITE_JPEG_QUALITY, 90])
    fmt_files = [
        str((fmt_dir / "sample.png").relative_to(ROOT)),
        str((fmt_dir / "sample.webp").relative_to(ROOT)),
        str((fmt_dir / "sample.jpg").relative_to(ROOT)),
    ]
    try:
        import pillow_heif
        from PIL import Image

        pillow_heif.register_heif_opener()
        rgb = cv2.cvtColor(scene, cv2.COLOR_BGR2RGB)
        Image.fromarray(rgb).save(str(fmt_dir / "sample.heic"), format="HEIF")
        fmt_files.append(str((fmt_dir / "sample.heic").relative_to(ROOT)))
    except Exception as exc:
        print(f"HEIC sample skipped: {exc}")
    categories["formats"] = fmt_files

    meta["categories"] = categories
    meta["human_labels"] = {
        "clear": "人工：清晰、曝光正常、低噪",
        "blur": "人工：不同程度模糊，越大的 kernel 越模糊",
        "overexpose": "人工：过曝/高光溢出，gain 越大越严重",
        "underexpose": "人工：欠曝/偏暗，gain 越小越暗",
        "noise": "人工：噪点随 sigma 递增",
        "counterexample": (
            "人工：①颗粒噪点重但 Laplacian 虚高 "
            "②过度锐化产生光晕但清晰度分高 "
            "③雾天低对比但曝光指标正常"
        ),
    }

    (OUT / "manifest.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta


if __name__ == "__main__":
    result = generate_all()
    print(f"Generated samples under {OUT}")
    for cat, files in result["categories"].items():
        print(f"  {cat}: {len(files)} files")
