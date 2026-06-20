"""Flet mobile-friendly UI: pick image, preview, analyze quality."""

from __future__ import annotations

import base64
import io
import sys
from pathlib import Path

import cv2
import flet as ft
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import os
import threading
from src.analyzer.decoder import PREVIEW_MAX_EDGE, decode_image, format_comparison_text  # noqa: E402
from src.analyzer.dl_scorer import is_dl_available  # noqa: E402
from src.analyzer.scorer import METHOD_LABELS, QualityReport, analyze_image  # noqa: E402
from src.analyzer import AIAnalyzerError, analyze_image_with_ai  # noqa: E402

# ── Design tokens ─────────────────────────────────────────────────────────────
_BG = "#0B0D12"
_SURFACE = "#151820"
_SURFACE_ALT = "#1C2030"
_BORDER = "#2A3042"
_TEXT = "#E8ECF4"
_TEXT_MUTED = "#8B93A8"
_ACCENT = "#6366F1"
_ACCENT_GRADIENT = ("#4F46E5", "#7C3AED")

_DIM_ICONS = {
    "sharpness": ft.Icons.CENTER_FOCUS_STRONG,
    "exposure": ft.Icons.WB_SUNNY_OUTLINED,
    "noise": ft.Icons.GRAIN,
    "contrast": ft.Icons.TONALITY,
    "deep_learning": ft.Icons.PSYCHOLOGY_OUTLINED,
}


def _bgr_to_png_bytes(bgr, max_edge: int = PREVIEW_MAX_EDGE) -> bytes:
    h, w = bgr.shape[:2]
    scale = min(1.0, max_edge / max(h, w))
    if scale < 1.0:
        bgr = cv2.resize(bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    return buf.getvalue()


# 1x1 透明 PNG，用于初始化 Image（Flet 0.85 要求 src 必须有效）
_PLACEHOLDER_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _score_color(score: float) -> str:
    if score >= 75:
        return "#34D399"
    if score >= 50:
        return "#FBBF24"
    return "#F87171"


def _card(content: ft.Control, *, padding: int = 20) -> ft.Container:
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=16,
        bgcolor=_SURFACE,
        border=ft.Border.all(1, _BORDER),
    )


def _section_label(text: str) -> ft.Text:
    return ft.Text(text, size=13, weight=ft.FontWeight.W_600, color=_TEXT_MUTED)


def _build_header() -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.HIGH_QUALITY, size=28, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.WHITE),
                    border_radius=14,
                    padding=14,
                ),
                ft.Column(
                    [
                        ft.Text("AI 图像画质分析", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text(
                            "JPEG · PNG · WebP · HEIC  |  传统 CV / 深度学习  |  离线可用",
                            size=12,
                            color=ft.Colors.with_opacity(0.82, ft.Colors.WHITE),
                        ),
                    ],
                    spacing=4,
                    expand=True,
                ),
            ],
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=24, vertical=22),
        border_radius=20,
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment.CENTER_LEFT,
            end=ft.alignment.Alignment.CENTER_RIGHT,
            colors=list(_ACCENT_GRADIENT),
        ),
    )


def _build_score_ring(score: float, grade: str) -> ft.Container:
    ring_color = _score_color(score)
    return ft.Container(
        content=ft.Stack(
            [
                ft.ProgressRing(
                    value=score / 100,
                    width=132,
                    height=132,
                    stroke_width=8,
                    color=ring_color,
                    bgcolor=ft.Colors.with_opacity(0.12, ring_color),
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                str(int(round(score))),
                                size=40,
                                weight=ft.FontWeight.BOLD,
                                color=ring_color,
                            ),
                            ft.Text("/ 100", size=13, color=_TEXT_MUTED),
                            ft.Text(grade, size=14, weight=ft.FontWeight.W_600, color=_TEXT),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                    ),
                    width=132,
                    height=132,
                    alignment=ft.alignment.Alignment.CENTER,
                ),
            ],
            width=132,
            height=132,
        ),
        width=132,
        height=132,
        alignment=ft.alignment.Alignment.CENTER,
    )


def _build_dimension_row(d) -> ft.Container:
    icon = _DIM_ICONS.get(d.name, ft.Icons.ANALYTICS_OUTLINED)
    color = _score_color(d.score)
    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(icon, size=18, color=color),
                            bgcolor=ft.Colors.with_opacity(0.12, color),
                            border_radius=8,
                            padding=8,
                        ),
                        ft.Column(
                            [
                                ft.Text(d.name_cn, weight=ft.FontWeight.W_600, size=14, color=_TEXT),
                                ft.Text(d.label, size=11, color=_TEXT_MUTED),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Text(f"{d.score}", color=color, weight=ft.FontWeight.BOLD, size=16),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.ProgressBar(
                    value=d.score / 100,
                    color=color,
                    bgcolor=ft.Colors.with_opacity(0.15, _BORDER),
                    height=6,
                    border_radius=3,
                ),
            ],
            spacing=8,
        ),
        padding=14,
        border_radius=12,
        bgcolor=_SURFACE_ALT,
    )


def _build_report_view(report: QualityReport) -> ft.Column:
    info = report.image_info
    method_label = METHOD_LABELS.get(report.method, report.method)

    meta_chips = [
        ft.Container(
            content=ft.Text(info.format_name, size=11, color=_TEXT_MUTED),
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.5, _SURFACE_ALT),
            border=ft.Border.all(1, _BORDER),
        ),
        ft.Container(
            content=ft.Text(f"{info.width}×{info.height}", size=11, color=_TEXT_MUTED),
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.5, _SURFACE_ALT),
            border=ft.Border.all(1, _BORDER),
        ),
        ft.Container(
            content=ft.Text(f"{info.megapixels} MP", size=11, color=_TEXT_MUTED),
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.5, _SURFACE_ALT),
            border=ft.Border.all(1, _BORDER),
        ),
        ft.Container(
            content=ft.Text(f"{info.file_size_kb:.0f} KB", size=11, color=_TEXT_MUTED),
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.5, _SURFACE_ALT),
            border=ft.Border.all(1, _BORDER),
        ),
    ]

    hybrid_note = None
    if report.method == "hybrid" and report.traditional_score is not None and report.dl_score is not None:
        hybrid_note = ft.Text(
            f"传统 {report.traditional_score} + 深度学习 {report.dl_score} → 综合 {report.overall_score}",
            size=11,
            color=_TEXT_MUTED,
            text_align=ft.TextAlign.CENTER,
        )

    overall_content: list[ft.Control] = [
        ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("综合画质评分", size=15, weight=ft.FontWeight.BOLD, color=_TEXT),
                        ft.Text(
                            f"{method_label} · {report.elapsed_ms:.0f} ms",
                            size=11,
                            color=_TEXT_MUTED,
                        ),
                    ],
                    spacing=4,
                    expand=True,
                ),
                _build_score_ring(report.overall_score, report.grade),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    ]
    if hybrid_note is not None:
        overall_content.append(hybrid_note)

    overall_card = _card(
        ft.Column(overall_content, spacing=12),
        padding=20,
    )

    dim_section = ft.Column(
        [
            _section_label("各维度得分"),
            *[_build_dimension_row(d) for d in report.dimensions],
        ],
        spacing=10,
    )

    summary = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.TIPS_AND_UPDATES_OUTLINED, size=18, color=_ACCENT),
                ft.Text(report.summary, size=13, color=_TEXT, expand=True),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        padding=16,
        border_radius=12,
        bgcolor=ft.Colors.with_opacity(0.08, _ACCENT),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.25, _ACCENT)),
    )

    return ft.Column(
        [
            ft.Row(meta_chips, wrap=True, spacing=8, run_spacing=8),
            overall_card,
            dim_section,
            summary,
        ],
        spacing=16,
    )


def main(page: ft.Page):
    page.title = "画质分析工具"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed=_ACCENT, visual_density=ft.VisualDensity.COMFORTABLE)
    page.bgcolor = _BG
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    preview_image = ft.Image(
        src=_PLACEHOLDER_PNG,
        fit=ft.BoxFit.CONTAIN,
        height=280,
        visible=False,
        border_radius=12,
    )
    preview_placeholder = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.IMAGE_OUTLINED, size=48, color=_TEXT_MUTED),
                ft.Text("分析后将在此显示图片预览", size=13, color=_TEXT_MUTED),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        height=280,
        alignment=ft.alignment.Alignment.CENTER,
        border_radius=12,
        bgcolor=_SURFACE_ALT,
        border=ft.Border.all(1, _BORDER),
    )
    preview_stack = ft.Stack([preview_placeholder, preview_image])

    status_icon = ft.Icon(ft.Icons.INFO_OUTLINED, size=16, color=_TEXT_MUTED)
    status_text = ft.Text("请选择一张本地图片进行分析", size=13, color=_TEXT_MUTED, expand=True)
    status_bar = ft.Container(
        content=ft.Row([status_icon, status_text], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
        border_radius=10,
        bgcolor=_SURFACE_ALT,
        border=ft.Border.all(1, _BORDER),
    )
    loading_ring = ft.ProgressRing(width=18, height=18, stroke_width=2, color=_ACCENT, visible=False)

    report_container = ft.Column(spacing=8)
    format_info = ft.Text(format_comparison_text(), size=12, color=_TEXT_MUTED)

    path_input = ft.TextField(
        label="图片路径",
        hint_text=r"例如：C:\Users\12777\Pictures\demo.jpg",
        border_radius=12,
        filled=True,
        bgcolor=_SURFACE_ALT,
        border_color=_BORDER,
        focused_border_color=_ACCENT,
        expand=True,
    )

    dl_ready = is_dl_available()
    method_group = ft.RadioGroup(
        value="traditional",
        content=ft.Row(
            [
                ft.Radio(value="traditional", label="传统算法", fill_color=_ACCENT),
                ft.Radio(value="dl", label="深度学习", fill_color=_ACCENT, disabled=not dl_ready),
                ft.Radio(value="hybrid", label="混合模式", fill_color=_ACCENT, disabled=not dl_ready),
            ],
            wrap=True,
            spacing=16,
        ),
    )
    dl_hint = ft.Row(
        [
            ft.Icon(
                ft.Icons.CHECK_CIRCLE_OUTLINE if dl_ready else ft.Icons.WARNING_AMBER_OUTLINED,
                size=14,
                color="#34D399" if dl_ready else "#FBBF24",
            ),
            ft.Text(
                "深度学习模式已就绪（pyiqa + CPU 推理）" if dl_ready else "深度学习未安装：pip install -r requirements-dl.txt",
                size=11,
                color="#34D399" if dl_ready else "#FBBF24",
            ),
        ],
        spacing=6,
    )

    def _set_status(message: str, *, kind: str = "info", loading: bool = False):
        icons = {
            "info": (ft.Icons.INFO_OUTLINED, _TEXT_MUTED),
            "loading": (ft.Icons.HOURGLASS_EMPTY, _ACCENT),
            "success": (ft.Icons.CHECK_CIRCLE_OUTLINE, "#34D399"),
            "error": (ft.Icons.ERROR_OUTLINE, "#F87171"),
        }
        icon_name, color = icons.get(kind, icons["info"])
        status_icon.name = icon_name
        status_icon.color = color
        status_text.value = message
        status_text.color = color if kind in ("success", "error") else _TEXT_MUTED
        loading_ring.visible = loading

    def on_analyze(source: str | bytes):
        method = method_group.value or "traditional"
        try:
            _set_status(f"正在解码与分析（{METHOD_LABELS.get(method, method)}）...", kind="loading", loading=True)
            analyze_btn.disabled = True
            preview_placeholder.visible = False
            page.update()
            report = analyze_image(source, method=method)
            preview_bgr, info = decode_image(source, for_analysis=False, max_edge=PREVIEW_MAX_EDGE)
            preview_image.src = _bgr_to_png_bytes(preview_bgr, max_edge=PREVIEW_MAX_EDGE)
            preview_image.visible = True
            report_container.controls = [_build_report_view(report)]
            _set_status(
                f"分析完成 · {info.width}×{info.height} ({info.megapixels} MP) · {report.image_info.decode_note}",
                kind="success",
            )
        except Exception as exc:
            _set_status(f"错误：{exc}", kind="error")
            report_container.controls = []
            preview_image.visible = False
            preview_placeholder.visible = True
        finally:
            analyze_btn.disabled = False
            loading_ring.visible = False
        page.update()

    def analyze_path(_: ft.ControlEvent):
        raw_path = (path_input.value or "").strip().strip('"')
        if not raw_path:
            _set_status("请先输入本地图片路径", kind="error")
            page.update()
            return
        candidate = Path(raw_path)
        if not candidate.exists():
            _set_status(f"文件不存在：{candidate}", kind="error")
            page.update()
            return
        if not candidate.is_file():
            _set_status(f"不是文件：{candidate}", kind="error")
            page.update()
            return
        on_analyze(str(candidate))

    analyze_btn = ft.FilledButton(
        "开始分析",
        icon=ft.Icons.AUTO_AWESOME,
        on_click=analyze_path,
        style=ft.ButtonStyle(
            bgcolor=_ACCENT,
            color=ft.Colors.WHITE,
            padding=ft.Padding.symmetric(horizontal=24, vertical=14),
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
    )

    input_card = _card(
        ft.Column(
            [
                _section_label("选择图片"),
                path_input,
                ft.Row(
                    [analyze_btn, loading_ring],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=12,
                ),
            ],
            spacing=14,
        ),
    )

    method_card = _card(
        ft.Column(
            [
                _section_label("评分模式"),
                method_group,
                dl_hint,
            ],
            spacing=12,
        ),
    )

    preview_card = _card(
        ft.Column(
            [
                _section_label("图片预览"),
                preview_stack,
            ],
            spacing=12,
        ),
        padding=16,
    )

    # ── AI 识图与分析 UI ────────────────────────────────────────────────────────
    DEFAULT_PROMPT = (
        "请对这张图片进行详细的画质与视觉分析，包括以下几个维度：\n"
        "1. 画面内容与主体识别：描述画面中主要展示的场景、物体或人物。\n"
        "2. 构图与美学：分析画面的构图方式（如三分法则、对称、引导线等）及美学风格。\n"
        "3. 光影与色彩：评估曝光度、明暗对比、色彩饱和度及色调搭配。\n"
        "4. 画质缺陷诊断：指出是否存在明显的噪点、模糊、镜头畸变、过度压缩等问题。\n"
        "5. 改进建议：针对以上画质和美学问题，提出具体的拍摄或后期处理改进建议。"
    )

    api_key_input = ft.TextField(
        label="Gemini API Key",
        password=True,
        can_reveal_password=True,
        filled=True,
        bgcolor=_SURFACE_ALT,
        border_color=_BORDER,
        focused_border_color=_ACCENT,
        expand=True,
    )

    def save_api_key(_):
        try:
            page.client_storage.set("gemini_api_key", api_key_input.value)
            _set_status("API Key 已成功保存", kind="success")
        except Exception:
            _set_status("API Key 已加载到当前会话（本地持久化不可用）", kind="success")
        page.update()

    model_dropdown = ft.Dropdown(
        label="模型选择",
        options=[
            ft.dropdown.Option("gemini-2.5-flash"),
            ft.dropdown.Option("gemini-2.0-flash"),
            ft.dropdown.Option("gemini-1.5-flash"),
            ft.dropdown.Option("gemini-1.5-pro"),
        ],
        value="gemini-2.5-flash",
        filled=True,
        bgcolor=_SURFACE_ALT,
        border_color=_BORDER,
        focused_border_color=_ACCENT,
    )

    prompt_input = ft.TextField(
        label="自定义分析提示词",
        multiline=True,
        min_lines=3,
        max_lines=6,
        value=DEFAULT_PROMPT,
        filled=True,
        bgcolor=_SURFACE_ALT,
        border_color=_BORDER,
        focused_border_color=_ACCENT,
    )

    # 加载已保存的 API Key
    try:
        saved_key = page.client_storage.get("gemini_api_key")
    except Exception:
        saved_key = None
    if saved_key:
        api_key_input.value = saved_key
    else:
        env_key = os.environ.get("GEMINI_API_KEY", "")
        if env_key:
            api_key_input.value = env_key

    ai_settings_tile = ft.ExpansionTile(
        title=ft.Text("AI 配置与提示词", size=13, weight=ft.FontWeight.W_600, color=_TEXT),
        subtitle=ft.Text("设置 API Key、模型和自定义 Prompt", size=11, color=_TEXT_MUTED),
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                api_key_input,
                                ft.IconButton(
                                    icon=ft.Icons.SAVE,
                                    tooltip="保存 API Key",
                                    icon_color=_ACCENT,
                                    on_click=save_api_key,
                                )
                            ],
                            spacing=8,
                        ),
                        model_dropdown,
                        prompt_input,
                    ],
                    spacing=12,
                ),
                padding=ft.Padding.only(left=8, right=8, bottom=12),
            )
        ],
        expanded=False,
        collapsed_text_color=_TEXT,
        text_color=_TEXT,
        icon_color=_TEXT_MUTED,
    )

    ai_markdown = ft.Markdown(
        value="",
        selectable=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
        code_theme="atom-one-dark",
    )

    ai_output_container = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.ASSISTANT, color=_ACCENT, size=18),
                        ft.Text("AI 视觉分析报告", size=15, weight=ft.FontWeight.BOLD, color=_TEXT),
                    ],
                    spacing=10,
                ),
                ft.Divider(color=_BORDER, height=1),
                ai_markdown,
            ],
            spacing=12,
        ),
        padding=16,
        border_radius=12,
        bgcolor=_SURFACE_ALT,
        border=ft.Border.all(1, _BORDER),
        visible=False,
    )

    ai_loading_ring = ft.ProgressRing(width=18, height=18, stroke_width=2, color=_ACCENT, visible=False)

    def on_ai_analyze(_: ft.ControlEvent):
        raw_path = (path_input.value or "").strip().strip('"')
        if not raw_path:
            _set_status("请先输入本地图片路径", kind="error")
            page.update()
            return
        candidate = Path(raw_path)
        if not candidate.exists() or not candidate.is_file():
            _set_status(f"文件不存在或不是有效文件：{candidate}", kind="error")
            page.update()
            return

        api_key = (api_key_input.value or "").strip()
        if not api_key:
            _set_status("请输入 Gemini API Key", kind="error")
            page.update()
            return

        ai_analyze_btn.disabled = True
        ai_loading_ring.visible = True
        _set_status("正在发送图片至 Gemini API 进行分析...", kind="loading", loading=True)
        page.update()

        def run_ai_task():
            try:
                result_text = analyze_image_with_ai(
                    source=str(candidate),
                    api_key=api_key,
                    model_name=model_dropdown.value or "gemini-2.5-flash",
                    prompt=prompt_input.value or DEFAULT_PROMPT
                )
                ai_markdown.value = result_text
                ai_output_container.visible = True
                _set_status("AI 识图分析完成", kind="success")
            except Exception as exc:
                ai_markdown.value = ""
                ai_output_container.visible = False
                _set_status(f"AI 分析失败: {exc}", kind="error")
            finally:
                ai_analyze_btn.disabled = False
                ai_loading_ring.visible = False
                page.update()

        threading.Thread(target=run_ai_task, daemon=True).start()

    ai_analyze_btn = ft.FilledButton(
        "开始 AI 识图",
        icon=ft.Icons.PSYCHOLOGY,
        on_click=on_ai_analyze,
        style=ft.ButtonStyle(
            bgcolor="#4F46E5",
            color=ft.Colors.WHITE,
            padding=ft.Padding.symmetric(horizontal=24, vertical=14),
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
    )

    ai_card = _card(
        ft.Column(
            [
                _section_label("AI 识图与分析 (Gemini)"),
                ai_settings_tile,
                ft.Row(
                    [ai_analyze_btn, ai_loading_ring],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=12,
                ),
                ai_output_container,
            ],
            spacing=14,
        )
    )

    format_expander = ft.ExpansionTile(
        title=ft.Text("格式说明", size=13, weight=ft.FontWeight.W_600, color=_TEXT),
        subtitle=ft.Text("支持的图片格式与解码说明", size=11, color=_TEXT_MUTED),
        controls=[ft.Container(content=format_info, padding=ft.Padding.only(left=4, bottom=8))],
        expanded=False,
        collapsed_text_color=_TEXT,
        text_color=_TEXT,
        icon_color=_TEXT_MUTED,
    )

    content = ft.Container(
        content=ft.Column(
            [
                _build_header(),
                method_card,
                input_card,
                ft.Row([status_bar], spacing=0),
                preview_card,
                report_container,
                ai_card,
                _card(format_expander, padding=8),
            ],
            spacing=16,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=20),
        width=min(720, page.width) if page.width else 720,
    )

    page.add(ft.Row([content], alignment=ft.MainAxisAlignment.CENTER))


if __name__ == "__main__":
    ft.run(main)
