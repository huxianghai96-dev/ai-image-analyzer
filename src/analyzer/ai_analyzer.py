"""AI-based image analysis and recognition using Gemini API."""

from __future__ import annotations

import io
from typing import Union
from PIL import Image

class AIAnalyzerError(RuntimeError):
    """Raised when AI analysis fails."""

def analyze_image_with_ai(
    source: Union[str, bytes],
    api_key: str,
    model_name: str = "gemini-2.5-flash",
    prompt: str = ""
) -> str:
    """
    Sends the image to Gemini API along with a custom prompt for visual analysis.
    
    Args:
        source: File path (str) or raw file bytes (bytes) of the image.
        api_key: Google Gemini API Key.
        model_name: The model identifier (e.g., 'gemini-2.5-flash').
        prompt: Instructions for the model.
        
    Returns:
        The markdown-formatted string returned by the model.
    """
    if not api_key or not api_key.strip():
        raise AIAnalyzerError("未配置 Gemini API Key，请先在配置面板中输入并保存。")

    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise AIAnalyzerError(
            "未安装 google-generativeai 依赖，请在终端执行 'pip install google-generativeai'。"
        ) from exc

    try:
        genai.configure(api_key=api_key.strip())
        model = genai.GenerativeModel(model_name)
    except Exception as exc:
        raise AIAnalyzerError(f"配置/创建 Gemini 客户端失败：{exc}") from exc

    try:
        if isinstance(source, bytes):
            image = Image.open(io.BytesIO(source))
        else:
            image = Image.open(source)
    except Exception as exc:
        raise AIAnalyzerError(f"读取图片失败，可能是文件损坏或格式不受支持：{exc}") from exc

    # Ensure the image is in RGB format for Gemini API, since PNG/HEIC might contain alpha
    try:
        if image.mode != "RGB":
            image = image.convert("RGB")
    except Exception as exc:
        raise AIAnalyzerError(f"转换图片颜色通道失败：{exc}") from exc

    # Downscale image if it is too large for general LLM input to save bandwidth and speed up request
    try:
        max_edge = 2048
        w, h = image.size
        if max(w, h) > max_edge:
            scale = max_edge / max(w, h)
            new_size = (int(w * scale), int(h * scale))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
    except Exception as exc:
        # Fallback to original if resize fails
        pass

    # Convert image to JPEG bytes to avoid format compatibility issues
    # (e.g., the google-generativeai library doesn't handle WebP format natively)
    try:
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="JPEG", quality=90)
        img_bytes = img_buffer.getvalue()
    except Exception as exc:
        raise AIAnalyzerError(f"转换图片为 JPEG 格式失败：{exc}") from exc

    try:
        image_part = {
            "mime_type": "image/jpeg",
            "data": img_bytes,
        }
        response = model.generate_content([prompt, image_part])
        if not response.text:
            raise AIAnalyzerError("Gemini 服务返回了空的内容，请尝试更换提示词。")
        return response.text
    except AIAnalyzerError:
        raise
    except Exception as exc:
        raise AIAnalyzerError(f"API 调用发生错误：{exc}") from exc
