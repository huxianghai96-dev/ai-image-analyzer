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
_BG = "#06080D"
_SURFACE = "#0F1219"
_SURFACE_HOVER = "#151A24"
_SURFACE_ALT = "#181D28"
_SURFACE_ELEVATED = "#1E2433"
_BORDER = "#232B3E"
_BORDER_SUBTLE = "#1A2035"
_TEXT = "#E8ECF4"
_TEXT_SECONDARY = "#B0B8CC"
_TEXT_MUTED = "#6B7490"
_ACCENT = "#818CF8"
_ACCENT_BRIGHT = "#A5B4FC"
_ACCENT_DIM = "#4F46E5"
_ACCENT_GLOW = "#6366F120"
_GRADIENT_START = "#4338CA"
_GRADIENT_MID = "#6366F1"
_GRADIENT_END = "#8B5CF6"

_SUCCESS = "#34D399"
_SUCCESS_DIM = "#059669"
_WARNING = "#FBBF24"
_WARNING_DIM = "#D97706"
_ERROR = "#F87171"
_ERROR_DIM = "#DC2626"

_DIM_ICONS = {
    "sharpness": ft.Icons.CENTER_FOCUS_STRONG,
    "exposure": ft.Icons.WB_SUNNY_OUTLINED,
    "noise": ft.Icons.GRAIN,
    "contrast": ft.Icons.TONALITY,
    "deep_learning": ft.Icons.PSYCHOLOGY_OUTLINED,
}

_DIM_COLORS = {
    "sharpness": "#60A5FA",
    "exposure": "#FBBF24",
    "noise": "#F472B6",
    "contrast": "#34D399",
    "deep_learning": "#A78BFA",
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
    if score >= 80:
        return _SUCCESS
    if score >= 60:
        return _WARNING
    return _ERROR


def _score_bg(score: float) -> str:
    if score >= 80:
        return _SUCCESS_DIM
    if score >= 60:
        return _WARNING_DIM
    return _ERROR_DIM


def _card(content: ft.Control, *, padding: int = 24) -> ft.Container:
    """Glassmorphism-style card with subtle border glow."""
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=20,
        bgcolor=_SURFACE,
        border=ft.Border.all(1, _BORDER_SUBTLE),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=24,
            color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
            offset=ft.Offset(0, 8),
        ),
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )


def _section_label(text: str) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(width=3, height=14, border_radius=2, bgcolor=_ACCENT),
                ft.Text(text, size=13, weight=ft.FontWeight.W_700, color=_TEXT_SECONDARY),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        margin=ft.Margin.only(bottom=4),
    )


def _build_header() -> ft.Container:
    """Premium animated gradient header."""
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.AUTO_AWESOME, size=26, color=ft.Colors.WHITE),
                    width=56,
                    height=56,
                    bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                    border_radius=16,
                    alignment=ft.alignment.Alignment.CENTER,
                    border=ft.Border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE)),
                ),
                ft.Column(
                    [
                        ft.Text(
                            "AI 图像画质分析",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Text(
                            "JPEG · PNG · WebP · HEIC  ·  传统 CV / 深度学习  ·  离线可用",
                            size=12,
                            color=ft.Colors.with_opacity(0.78, ft.Colors.WHITE),
                        ),
                    ],
                    spacing=6,
                    expand=True,
                ),
            ],
            spacing=18,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=28, vertical=26),
        border_radius=24,
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment.TOP_LEFT,
            end=ft.alignment.Alignment.BOTTOM_RIGHT,
            colors=[_GRADIENT_START, _GRADIENT_MID, _GRADIENT_END],
            tile_mode=ft.GradientTileMode.CLAMP,
        ),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=40,
            color=ft.Colors.with_opacity(0.3, _GRADIENT_MID),
            offset=ft.Offset(0, 12),
        ),
    )


def _build_score_ring(score: float, grade: str) -> ft.Container:
    ring_color = _score_color(score)
    return ft.Container(
        content=ft.Stack(
            [
                # Glow background
                ft.Container(
                    width=140,
                    height=140,
                    border_radius=70,
                    bgcolor=ft.Colors.with_opacity(0.06, ring_color),
                ),
                ft.ProgressRing(
                    value=score / 100,
                    width=140,
                    height=140,
                    stroke_width=7,
                    color=ring_color,
                    bgcolor=ft.Colors.with_opacity(0.08, ring_color),
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                str(int(round(score))),
                                size=42,
                                weight=ft.FontWeight.BOLD,
                                color=ring_color,
                            ),
                            ft.Text("/ 100", size=12, color=_TEXT_MUTED, weight=ft.FontWeight.W_500),
                            ft.Container(
                                content=ft.Text(
                                    grade, size=11, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE,
                                ),
                                bgcolor=ft.Colors.with_opacity(0.2, ring_color),
                                border_radius=6,
                                padding=ft.Padding.symmetric(horizontal=10, vertical=3),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                    ),
                    width=140,
                    height=140,
                    alignment=ft.alignment.Alignment.CENTER,
                ),
            ],
            width=140,
            height=140,
        ),
        width=140,
        height=140,
        alignment=ft.alignment.Alignment.CENTER,
        animate_scale=ft.Animation(400, ft.AnimationCurve.EASE_OUT_BACK),
    )


def _build_dimension_row(d) -> ft.Container:
    icon = _DIM_ICONS.get(d.name, ft.Icons.ANALYTICS_OUTLINED)
    # Use unique color per dimension, fallback to score-based color
    accent = _DIM_COLORS.get(d.name, _score_color(d.score))
    color = _score_color(d.score)
    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(icon, size=18, color=accent),
                            bgcolor=ft.Colors.with_opacity(0.10, accent),
                            border_radius=10,
                            width=38,
                            height=38,
                            alignment=ft.alignment.Alignment.CENTER,
                        ),
                        ft.Column(
                            [
                                ft.Text(d.name_cn, weight=ft.FontWeight.W_600, size=14, color=_TEXT),
                                ft.Text(d.label, size=11, color=_TEXT_MUTED),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Text(
                                f"{d.score}",
                                color=color,
                                weight=ft.FontWeight.BOLD,
                                size=16,
                            ),
                            bgcolor=ft.Colors.with_opacity(0.08, color),
                            border_radius=8,
                            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                        ),
                    ],
                    spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(
                    content=ft.ProgressBar(
                        value=d.score / 100,
                        color=accent,
                        bgcolor=ft.Colors.with_opacity(0.08, _BORDER),
                        height=5,
                        border_radius=3,
                    ),
                    padding=ft.Padding.only(left=52),
                ),
            ],
            spacing=10,
        ),
        padding=16,
        border_radius=14,
        bgcolor=_SURFACE_ALT,
        border=ft.Border.all(1, _BORDER_SUBTLE),
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )


def _build_report_view(report: QualityReport) -> ft.Column:
    info = report.image_info
    method_label = METHOD_LABELS.get(report.method, report.method)

    def _meta_chip(icon, text):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=12, color=_TEXT_MUTED),
                    ft.Text(text, size=11, color=_TEXT_SECONDARY, weight=ft.FontWeight.W_500),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            border_radius=20,
            bgcolor=_SURFACE_ALT,
            border=ft.Border.all(1, _BORDER_SUBTLE),
        )

    meta_chips = [
        _meta_chip(ft.Icons.IMAGE_OUTLINED, info.format_name),
        _meta_chip(ft.Icons.ASPECT_RATIO, f"{info.width}×{info.height}"),
        _meta_chip(ft.Icons.CAMERA, f"{info.megapixels} MP"),
        _meta_chip(ft.Icons.SD_STORAGE, f"{info.file_size_kb:.0f} KB"),
    ]

    hybrid_note = None
    if report.method == "hybrid" and report.traditional_score is not None and report.dl_score is not None:
        hybrid_note = ft.Container(
            content=ft.Text(
                f"传统 {report.traditional_score} + 深度学习 {report.dl_score} → 综合 {report.overall_score}",
                size=11,
                color=_TEXT_SECONDARY,
                text_align=ft.TextAlign.CENTER,
                weight=ft.FontWeight.W_500,
            ),
            bgcolor=ft.Colors.with_opacity(0.06, _ACCENT),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
        )

    overall_content: list[ft.Control] = [
        ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("综合画质评分", size=16, weight=ft.FontWeight.BOLD, color=_TEXT),
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.TIMER_OUTLINED, size=12, color=_TEXT_MUTED),
                                    ft.Text(
                                        f"{method_label} · {report.elapsed_ms:.0f} ms",
                                        size=11,
                                        color=_TEXT_MUTED,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                ],
                                spacing=4,
                            ),
                        ),
                    ],
                    spacing=6,
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
        ft.Column(overall_content, spacing=14),
        padding=24,
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
                ft.Container(
                    content=ft.Icon(ft.Icons.TIPS_AND_UPDATES_OUTLINED, size=18, color=_ACCENT_BRIGHT),
                    bgcolor=ft.Colors.with_opacity(0.12, _ACCENT),
                    border_radius=10,
                    width=36,
                    height=36,
                    alignment=ft.alignment.Alignment.CENTER,
                ),
                ft.Text(report.summary, size=13, color=_TEXT_SECONDARY, expand=True),
            ],
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        padding=18,
        border_radius=16,
        bgcolor=ft.Colors.with_opacity(0.05, _ACCENT),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.15, _ACCENT)),
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
    page.title = "AI 画质分析工具"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(
        color_scheme_seed=_ACCENT,
        visual_density=ft.VisualDensity.COMFORTABLE,
    )
    page.bgcolor = _BG
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    # ── State ─────────────────────────────────────────────────────────────────
    current_source: dict = {"path": None}  # mutable container for closure

    # ── FilePicker (Flet 0.85+ Service, do NOT add to page.overlay) ───────────
    file_picker = ft.FilePicker()

    # ── Preview area ──────────────────────────────────────────────────────────
    preview_image = ft.Image(
        src=_PLACEHOLDER_PNG,
        fit=ft.BoxFit.CONTAIN,
        height=300,
        visible=False,
        border_radius=16,
    )

    # ── Empty-state onboarding (shown before any image is selected) ───────────
    preview_placeholder = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED, size=48, color=_ACCENT_BRIGHT),
                    width=88,
                    height=88,
                    border_radius=24,
                    bgcolor=ft.Colors.with_opacity(0.08, _ACCENT),
                    alignment=ft.alignment.Alignment.CENTER,
                    border=ft.Border.all(1, ft.Colors.with_opacity(0.15, _ACCENT)),
                ),
                ft.Text("点击下方按钮选择图片", size=15, color=_TEXT_SECONDARY, weight=ft.FontWeight.W_600),
                ft.Text(
                    "支持 JPEG · PNG · WebP · HEIC  |  本地相册或文件",
                    size=12,
                    color=ft.Colors.with_opacity(0.5, _TEXT_MUTED),
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=4),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text("≥ 12MP 大图安全加载", size=10, color=_SUCCESS,
                                            weight=ft.FontWeight.W_500),
                            bgcolor=ft.Colors.with_opacity(0.08, _SUCCESS),
                            border_radius=12,
                            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                        ),
                        ft.Container(
                            content=ft.Text("离线可用", size=10, color=_ACCENT_BRIGHT,
                                            weight=ft.FontWeight.W_500),
                            bgcolor=ft.Colors.with_opacity(0.08, _ACCENT),
                            border_radius=12,
                            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        ),
        height=300,
        alignment=ft.alignment.Alignment.CENTER,
        border_radius=16,
        bgcolor=_SURFACE_ALT,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.15, _ACCENT)),
    )
    preview_stack = ft.Stack([preview_placeholder, preview_image])

    # ── Status bar ────────────────────────────────────────────────────────────
    status_icon = ft.Icon(ft.Icons.INFO_OUTLINED, size=15, color=_TEXT_MUTED)
    status_text = ft.Text(
        "请选择一张本地图片进行分析", size=13, color=_TEXT_MUTED,
        expand=True, weight=ft.FontWeight.W_500,
    )
    status_bar = ft.Container(
        content=ft.Row(
            [status_icon, status_text],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
        border_radius=12,
        bgcolor=_SURFACE_ALT,
        border=ft.Border.all(1, _BORDER_SUBTLE),
        animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
    )
    loading_ring = ft.ProgressRing(width=18, height=18, stroke_width=2, color=_ACCENT, visible=False)

    report_container = ft.Column(spacing=8)
    format_info = ft.Text(format_comparison_text(), size=12, color=_TEXT_MUTED)

    # ── Selected file display ─────────────────────────────────────────────────
    selected_file_text = ft.Text("", size=12, color=_TEXT_SECONDARY, weight=ft.FontWeight.W_500, expand=True)
    selected_file_row = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.INSERT_DRIVE_FILE_OUTLINED, size=14, color=_ACCENT),
                selected_file_text,
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=14, vertical=8),
        border_radius=10,
        bgcolor=ft.Colors.with_opacity(0.06, _ACCENT),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.12, _ACCENT)),
        visible=False,
    )

    # ── Path input (alternative / desktop fallback) ───────────────────────────
    path_input = ft.TextField(
        label="或输入图片路径",
        hint_text=r"例如：C:\Users\Pictures\demo.jpg",
        border_radius=14,
        filled=True,
        bgcolor=_SURFACE_ALT,
        border_color=_BORDER,
        focused_border_color=_ACCENT,
        cursor_color=_ACCENT,
        label_style=ft.TextStyle(color=_TEXT_MUTED),
        text_size=13,
        expand=True,
    )

    # ── Method selection ──────────────────────────────────────────────────────
    dl_ready = is_dl_available()

    def _method_chip(value: str, label: str, icon: str, disabled: bool = False):
        return ft.Radio(
            value=value,
            label=label,
            fill_color={
                ft.ControlState.SELECTED: _ACCENT,
                ft.ControlState.DEFAULT: _BORDER,
            },
            disabled=disabled,
        )

    method_group = ft.RadioGroup(
        value="traditional",
        content=ft.Row(
            [
                _method_chip("traditional", "传统算法", ft.Icons.ANALYTICS),
                _method_chip("dl", "深度学习", ft.Icons.PSYCHOLOGY, disabled=not dl_ready),
                _method_chip("hybrid", "混合模式", ft.Icons.MERGE_TYPE, disabled=not dl_ready),
            ],
            wrap=True,
            spacing=20,
        ),
    )
    dl_hint = ft.Container(
        content=ft.Row(
            [
                ft.Icon(
                    ft.Icons.CHECK_CIRCLE if dl_ready else ft.Icons.WARNING_AMBER_OUTLINED,
                    size=14,
                    color=_SUCCESS if dl_ready else _WARNING,
                ),
                ft.Text(
                    "深度学习模式已就绪（pyiqa + CPU 推理）" if dl_ready else "深度学习未安装：pip install -r requirements-dl.txt",
                    size=11,
                    color=_SUCCESS if dl_ready else _WARNING,
                    weight=ft.FontWeight.W_500,
                ),
            ],
            spacing=8,
        ),
        bgcolor=ft.Colors.with_opacity(0.06, _SUCCESS if dl_ready else _WARNING),
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=12, vertical=6),
    )

    # ── Status helpers ────────────────────────────────────────────────────────
    def _set_status(message: str, *, kind: str = "info", loading: bool = False):
        icons = {
            "info": (ft.Icons.INFO_OUTLINED, _TEXT_MUTED),
            "loading": (ft.Icons.HOURGLASS_EMPTY, _ACCENT),
            "success": (ft.Icons.CHECK_CIRCLE_OUTLINE, _SUCCESS),
            "error": (ft.Icons.ERROR_OUTLINE, _ERROR),
        }
        icon_name, color = icons.get(kind, icons["info"])
        status_icon.name = icon_name
        status_icon.color = color
        status_text.value = message
        status_text.color = color if kind in ("success", "error") else _TEXT_MUTED
        loading_ring.visible = loading
        # Animate status bar border color based on kind
        border_colors = {
            "info": _BORDER_SUBTLE,
            "loading": ft.Colors.with_opacity(0.3, _ACCENT),
            "success": ft.Colors.with_opacity(0.3, _SUCCESS),
            "error": ft.Colors.with_opacity(0.3, _ERROR),
        }
        status_bar.border = ft.Border.all(1, border_colors.get(kind, _BORDER_SUBTLE))

    # ── Core analyze callback ─────────────────────────────────────────────────
    def on_analyze(source: str | bytes):
        method = method_group.value or "traditional"
        try:
            _set_status(f"正在解码与分析（{METHOD_LABELS.get(method, method)}）...", kind="loading", loading=True)
            pick_btn.disabled = True
            analyze_path_btn.disabled = True
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
            pick_btn.disabled = False
            analyze_path_btn.disabled = False
            loading_ring.visible = False
        page.update()

    # ── Pick button click (Flet 0.85 async handling) ──────────────────────────
    async def on_pick_click(_: ft.ControlEvent):
        try:
            files = await file_picker.pick_files(
                dialog_title="选择图片",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["jpg", "jpeg", "png", "webp", "heic", "heif"],
                allow_multiple=False,
            )
        except Exception as exc:
            _set_status(f"文件选择器启动失败：{exc}", kind="error")
            page.update()
            return

        if not files or len(files) == 0:
            return  # user cancelled

        picked = files[0]
        file_path = picked.path
        if not file_path:
            _set_status("无法获取文件路径（移动端可能需要额外权限）", kind="error")
            page.update()
            return

        current_source["path"] = file_path
        fname = Path(file_path).name
        selected_file_text.value = fname
        selected_file_row.visible = True
        path_input.value = file_path
        _set_status(f"已选择：{fname}，正在分析...", kind="loading", loading=True)
        page.update()

        # Run analysis on background thread to keep UI responsive
        def _bg():
            on_analyze(file_path)
        page.run_thread(_bg)

    # ── Path input analyze ────────────────────────────────────────────────────
    def analyze_from_path(_: ft.ControlEvent):
        raw_path = (path_input.value or "").strip().strip('"')
        if not raw_path:
            _set_status("请先输入本地图片路径或点击「选择图片」", kind="error")
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
        current_source["path"] = str(candidate)
        selected_file_text.value = candidate.name
        selected_file_row.visible = True
        page.update()

        def _bg():
            on_analyze(str(candidate))
        page.run_thread(_bg)

    # ── Primary pick button (hero CTA) ────────────────────────────────────────
    pick_btn = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.PHOTO_LIBRARY_OUTLINED, size=20, color=ft.Colors.WHITE),
                ft.Text("选择图片", size=15, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=_ACCENT_DIM,
        border_radius=16,
        padding=ft.Padding.symmetric(horizontal=36, vertical=16),
        on_click=on_pick_click,
        ink=True,
        ink_color=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=24,
            color=ft.Colors.with_opacity(0.3, _ACCENT_DIM),
            offset=ft.Offset(0, 6),
        ),
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment.CENTER_LEFT,
            end=ft.alignment.Alignment.CENTER_RIGHT,
            colors=[_GRADIENT_START, _GRADIENT_MID],
        ),
    )

    # ── Analyze-from-path button ──────────────────────────────────────────────
    analyze_path_btn = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.AUTO_AWESOME, size=16, color=ft.Colors.WHITE),
                ft.Text("分析", size=13, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=_ACCENT_DIM,
        border_radius=12,
        padding=ft.Padding.symmetric(horizontal=20, vertical=12),
        on_click=analyze_from_path,
        ink=True,
        ink_color=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment.CENTER_LEFT,
            end=ft.alignment.Alignment.CENTER_RIGHT,
            colors=[_GRADIENT_MID, _GRADIENT_END],
        ),
    )

    # ── Input card (FilePicker + path fallback) ───────────────────────────────
    input_card = _card(
        ft.Column(
            [
                _section_label("选择图片"),
                # Primary: file picker button
                ft.Row(
                    [pick_btn],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                selected_file_row,
                # Divider with "or"
                ft.Row(
                    [
                        ft.Container(expand=True, height=1, bgcolor=_BORDER_SUBTLE),
                        ft.Text("或", size=11, color=_TEXT_MUTED, weight=ft.FontWeight.W_500),
                        ft.Container(expand=True, height=1, bgcolor=_BORDER_SUBTLE),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                # Secondary: path input
                ft.Row(
                    [
                        path_input,
                        analyze_path_btn,
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
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
            spacing=14,
        ),
    )

    preview_card = _card(
        ft.Column(
            [
                _section_label("图片预览"),
                preview_stack,
            ],
            spacing=14,
        ),
        padding=20,
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
        cursor_color=_ACCENT,
        border_radius=14,
        label_style=ft.TextStyle(color=_TEXT_MUTED),
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
        border_radius=14,
        label_style=ft.TextStyle(color=_TEXT_MUTED),
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
        cursor_color=_ACCENT,
        border_radius=14,
        label_style=ft.TextStyle(color=_TEXT_MUTED),
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
                                ft.Container(
                                    content=ft.Icon(ft.Icons.SAVE_OUTLINED, size=20, color=_ACCENT),
                                    on_click=save_api_key,
                                    tooltip="保存 API Key",
                                    ink=True,
                                    ink_color=ft.Colors.with_opacity(0.1, _ACCENT),
                                    border_radius=12,
                                    width=44,
                                    height=44,
                                    alignment=ft.alignment.Alignment.CENTER,
                                    bgcolor=ft.Colors.with_opacity(0.06, _ACCENT),
                                    border=ft.Border.all(1, ft.Colors.with_opacity(0.15, _ACCENT)),
                                ),
                            ],
                            spacing=10,
                        ),
                        model_dropdown,
                        prompt_input,
                    ],
                    spacing=14,
                ),
                padding=ft.Padding.only(left=8, right=8, bottom=14),
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
                        ft.Container(
                            content=ft.Icon(ft.Icons.ASSISTANT, color=_ACCENT_BRIGHT, size=18),
                            bgcolor=ft.Colors.with_opacity(0.10, _ACCENT),
                            border_radius=10,
                            width=36,
                            height=36,
                            alignment=ft.alignment.Alignment.CENTER,
                        ),
                        ft.Text("AI 视觉分析报告", size=15, weight=ft.FontWeight.BOLD, color=_TEXT),
                    ],
                    spacing=12,
                ),
                ft.Divider(color=_BORDER_SUBTLE, height=1),
                ai_markdown,
            ],
            spacing=14,
        ),
        padding=20,
        border_radius=16,
        bgcolor=_SURFACE_ALT,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.15, _ACCENT)),
        visible=False,
    )

    ai_loading_ring = ft.ProgressRing(width=18, height=18, stroke_width=2, color=_ACCENT, visible=False)

    def on_ai_analyze(_: ft.ControlEvent):
        source_path = current_source.get("path")
        if not source_path:
            raw_path = (path_input.value or "").strip().strip('"')
            if raw_path and Path(raw_path).is_file():
                source_path = raw_path
            else:
                _set_status("请先选择或输入一张图片", kind="error")
                page.update()
                return

        candidate = Path(source_path)
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

        page.run_thread(run_ai_task)

    ai_analyze_btn = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.PSYCHOLOGY, size=18, color=ft.Colors.WHITE),
                ft.Text("开始 AI 识图", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=_ACCENT_DIM,
        border_radius=14,
        padding=ft.Padding.symmetric(horizontal=28, vertical=14),
        on_click=on_ai_analyze,
        ink=True,
        ink_color=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=16,
            color=ft.Colors.with_opacity(0.2, _GRADIENT_END),
            offset=ft.Offset(0, 4),
        ),
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment.CENTER_LEFT,
            end=ft.alignment.Alignment.CENTER_RIGHT,
            colors=[_GRADIENT_MID, _GRADIENT_END],
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
                    spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ai_output_container,
            ],
            spacing=16,
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

    # ── Footer ────────────────────────────────────────────────────────────────
    footer = ft.Container(
        content=ft.Column(
            [
                ft.Divider(color=_BORDER_SUBTLE, height=1),
                ft.Row(
                    [
                        ft.Text(
                            "AI Image Quality Analyzer",
                            size=11,
                            color=ft.Colors.with_opacity(0.4, _TEXT_MUTED),
                            weight=ft.FontWeight.W_500,
                            italic=True,
                        ),
                        ft.Text(
                            "Powered by OpenCV · pyiqa · Gemini",
                            size=11,
                            color=ft.Colors.with_opacity(0.35, _TEXT_MUTED),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=12,
        ),
        padding=ft.Padding.only(top=8, bottom=20),
    )

    # ── Page layout ───────────────────────────────────────────────────────────
    content = ft.Container(
        content=ft.Column(
            [
                _build_header(),
                input_card,
                method_card,
                ft.Row(
                    [status_bar, loading_ring],
                    spacing=10,
                    expand=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                preview_card,
                report_container,
                ai_card,
                _card(format_expander, padding=10),
                footer,
            ],
            spacing=16,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=24),
        width=min(720, page.width) if page.width else 720,
    )

    page.add(ft.Row([content], alignment=ft.MainAxisAlignment.CENTER))


if __name__ == "__main__":
    ft.run(main)
