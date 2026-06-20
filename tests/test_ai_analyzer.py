"""Unit tests for the AI analyzer module."""

from __future__ import annotations

import io
import unittest
from unittest.mock import MagicMock, patch
import os

from PIL import Image
from src.analyzer.ai_analyzer import AIAnalyzerError, analyze_image_with_ai


class TestAIAnalyzer(unittest.TestCase):
    def setUp(self):
        # Create a small dummy image in memory for testing
        self.img_bytes = io.BytesIO()
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(self.img_bytes, format="PNG")
        self.img_bytes = self.img_bytes.getvalue()

    def test_missing_api_key(self):
        """Test that missing or empty API key raises AIAnalyzerError."""
        with self.assertRaises(AIAnalyzerError) as ctx:
            analyze_image_with_ai(self.img_bytes, api_key="")
        self.assertIn("未配置 Gemini API Key", str(ctx.exception))

        with self.assertRaises(AIAnalyzerError) as ctx:
            analyze_image_with_ai(self.img_bytes, api_key="   ")
        self.assertIn("未配置 Gemini API Key", str(ctx.exception))

    @patch("google.generativeai.GenerativeModel")
    @patch("google.generativeai.configure")
    def test_successful_analysis_mock(self, mock_configure, mock_model_class):
        """Test a successful AI analysis call using mocked Gemini client."""
        # Set up mock response
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is a beautiful blue image."
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        result = analyze_image_with_ai(
            source=self.img_bytes,
            api_key="mock_valid_api_key",
            model_name="gemini-2.5-flash",
            prompt="Describe this image."
        )

        # Assertions
        mock_configure.assert_called_once_with(api_key="mock_valid_api_key")
        mock_model_class.assert_called_once_with("gemini-2.5-flash")
        self.assertEqual(result, "This is a beautiful blue image.")

    @patch("google.generativeai.GenerativeModel")
    @patch("google.generativeai.configure")
    def test_empty_response_error(self, mock_configure, mock_model_class):
        """Test that an empty response raises an AIAnalyzerError."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = ""  # Empty response text
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        with self.assertRaises(AIAnalyzerError) as ctx:
            analyze_image_with_ai(
                source=self.img_bytes,
                api_key="mock_valid_api_key",
                model_name="gemini-2.5-flash",
                prompt="Describe this image."
            )
        self.assertIn("Gemini 服务返回了空的内容", str(ctx.exception))

    @patch("google.generativeai.GenerativeModel")
    @patch("google.generativeai.configure")
    def test_api_call_exception(self, mock_configure, mock_model_class):
        """Test that an API exception is wrapped in AIAnalyzerError."""
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API quota exceeded")
        mock_model_class.return_value = mock_model

        with self.assertRaises(AIAnalyzerError) as ctx:
            analyze_image_with_ai(
                source=self.img_bytes,
                api_key="mock_valid_api_key",
                model_name="gemini-2.5-flash",
                prompt="Describe this image."
            )
        self.assertIn("API 调用发生错误", str(ctx.exception))
        self.assertIn("API quota exceeded", str(ctx.exception))

    @unittest.skipUnless(os.environ.get("GEMINI_API_KEY"), "Requires GEMINI_API_KEY environment variable")
    def test_integration_real_api(self):
        """Integration test with a real Gemini API key and a sample image."""
        api_key = os.environ["GEMINI_API_KEY"]
        # Find a test sample in the workspace
        sample_path = os.path.join("test_samples", "formats", "sample.png")
        if not os.path.exists(sample_path):
            self.skipTest(f"Sample image not found at {sample_path}")

        try:
            result = analyze_image_with_ai(
                source=sample_path,
                api_key=api_key,
                model_name="gemini-2.5-flash",
                prompt="识别图中的色调和主要构图（请用中文简短回答在两句话以内）。"
            )
            print("\nReal API response content:\n", result)
            self.assertTrue(len(result) > 0)
        except AIAnalyzerError as exc:
            self.fail(f"Real API call failed: {exc}")


if __name__ == "__main__":
    unittest.main()
