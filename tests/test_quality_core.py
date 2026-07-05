"""Core decoder and image-quality scoring tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from src.analyzer.decoder import decode_image
from src.analyzer.scorer import analyze_ndarray


def _detail_image(size: int = 512) -> np.ndarray:
    img = np.full((size, size, 3), 128, dtype=np.uint8)
    cv2.rectangle(img, (40, 40), (size - 40, size - 40), (40, 180, 220), 4)
    cv2.line(img, (50, size - 80), (size - 50, 80), (240, 240, 240), 3)
    cv2.circle(img, (size // 2, size // 2), 90, (30, 60, 210), 3)
    cv2.putText(img, "QUALITY", (70, size // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.7, (20, 20, 20), 3)
    return img


class TestQualityCore(unittest.TestCase):
    def test_blur_reduces_sharpness_and_overall_score(self):
        sharp = _detail_image()
        blurred = cv2.GaussianBlur(sharp, (31, 31), 0)

        sharp_report = analyze_ndarray(sharp)
        blur_report = analyze_ndarray(blurred)

        sharp_dim = next(d for d in sharp_report.dimensions if d.name == "sharpness")
        blur_dim = next(d for d in blur_report.dimensions if d.name == "sharpness")

        self.assertGreater(sharp_dim.score, blur_dim.score + 20)
        self.assertGreater(sharp_report.overall_score, blur_report.overall_score)
        self.assertIn("模糊", blur_dim.label)

    def test_exposure_labels_over_and_under_exposed_images(self):
        base = np.full((256, 256, 3), 128, dtype=np.uint8)
        over = np.full_like(base, 255)
        under = np.zeros_like(base)

        over_report = analyze_ndarray(over)
        under_report = analyze_ndarray(under)

        over_dim = next(d for d in over_report.dimensions if d.name == "exposure")
        under_dim = next(d for d in under_report.dimensions if d.name == "exposure")

        self.assertEqual(over_dim.label, "过曝")
        self.assertEqual(under_dim.label, "欠曝")

    def test_decode_common_formats_and_downscale_large_images(self):
        image = _detail_image(768)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            paths = [
                tmp_path / "sample.jpg",
                tmp_path / "sample.png",
                tmp_path / "sample.webp",
            ]

            self.assertTrue(cv2.imwrite(str(paths[0]), image))
            self.assertTrue(cv2.imwrite(str(paths[1]), image))
            if not cv2.imwrite(str(paths[2]), image):
                self.skipTest("OpenCV WebP encoder is unavailable in this environment")

            for path in paths:
                decoded, info = decode_image(str(path), max_edge=256)
                self.assertLessEqual(max(decoded.shape[:2]), 256)
                self.assertGreater(info.megapixels, 0)
                self.assertIn(info.format_name, {"JPG", "JPEG", "PNG", "WEBP"})

    def test_decode_heic_when_codec_is_available(self):
        try:
            import pillow_heif
            from PIL import Image
        except ImportError:
            self.skipTest("pillow-heif is unavailable")

        image = _detail_image(256)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.heic"
            pillow_heif.register_heif_opener()
            Image.fromarray(rgb).save(path, format="HEIF")

            decoded, info = decode_image(str(path), max_edge=128)
            self.assertLessEqual(max(decoded.shape[:2]), 128)
            self.assertEqual(info.format_name, "HEIC")


if __name__ == "__main__":
    unittest.main()
