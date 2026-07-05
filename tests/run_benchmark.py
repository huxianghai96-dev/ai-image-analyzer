"""Run benchmark on test samples and export verification report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analyzer.dl_scorer import is_dl_available  # noqa: E402
from src.analyzer.scorer import METHOD_LABELS, analyze_image  # noqa: E402

SAMPLES = ROOT / "test_samples"
OUT = ROOT / "docs" / "verification"

METHODS = ("traditional", "dl", "hybrid")

HUMAN_EXPECTATION = {
    "clear": ("高", "综合分应 ≥ 70"),
    "blur": ("低", "综合分应随模糊加重而下降"),
    "overexpose": ("低", "曝光维度分应明显偏低"),
    "underexpose": ("低", "曝光维度分应明显偏低"),
    "noise": ("低", "噪点维度分应随 sigma 下降"),
    "large": ("中", "大图耗时可放宽，但应 < 2000ms"),
    "counterexample": ("失准", "至少 1 个维度评分与主观感受不符"),
    "formats": ("一致", "同内容不同格式分数应接近"),
}

# Detailed per-file human judgments for counterexamples
COUNTEREXAMPLE_ANALYSIS = {
    "noise_masquerade_sharp.jpg": {
        "human_quality": "差",
        "human_reason": "强颗粒噪点充斥画面，细节完全被噪点掩盖，主观画质差",
        "expected_failure": "Laplacian 方差因噪点高频能量而虚高，清晰度分可能 ≥ 80",
        "root_cause": (
            "Laplacian 算子检测的是二阶导数能量，无法区分「纹理边缘」和「随机噪点」。"
            "颗粒噪点（高 ISO 模拟）产生大量高频响应，方差被显著抬高。"
            "虽有噪点交叉校正（scorer.py），但当 noise_level 与 variance 均极高时，"
            "校正力度不足以完全消除虚高。"
        ),
    },
    "over_sharpened_halo.jpg": {
        "human_quality": "差",
        "human_reason": "过度 USM 锐化产生明显光晕和边缘伪影，视觉不自然",
        "expected_failure": "Laplacian 方差因锐化后的强边缘而极高，清晰度分接近满分",
        "root_cause": (
            "Unsharp Mask 锐化通过增强边缘对比度来提升「清晰感」，"
            "Laplacian 方差直接反映这种增强，因此打出高分。"
            "但过度锐化会产生 halo（光晕）和振铃效应，人眼感知为伪影而非真正清晰。"
            "当前算法缺乏对锐化伪影的检测（如 overshoot 检测）。"
        ),
    },
    "foggy_low_contrast.jpg": {
        "human_quality": "差",
        "human_reason": "雾天场景，画面发灰、对比度极低，细节不可辨",
        "expected_failure": "曝光维度可能正常（均值接近 128），但对比度和清晰度应偏低",
        "root_cause": (
            "曝光算法基于全局亮度均值和裁剪率，雾天场景亮度均值可能接近理想区间，"
            "因此曝光分不会很低。但人眼感知的是信息量（对比度、细节），"
            "而非仅仅是亮度。对比度维度（RMS）能捕捉到此问题，但权重仅 15%，"
            "可能不足以将综合分拉低到与主观感受一致的水平。"
        ),
    },
}


def _sample_entry(category: str, rel: str, method: str, report) -> dict:
    dim_map = {d.name: float(d.score) for d in report.dimensions}
    sharp_dim = next((d for d in report.dimensions if d.name == "sharpness"), None)
    raw_sharp = float(sharp_dim.details.get("score", sharp_dim.score)) if sharp_dim else None
    entry = {
        "category": category,
        "file": rel,
        "method": method,
        "overall": report.overall_score,
        "grade": report.grade,
        "elapsed_ms": report.elapsed_ms,
        "summary": report.summary,
        "dimensions": dim_map,
        "dl_score": report.dl_score,
        "traditional_score": report.traditional_score,
        "human_expectation": HUMAN_EXPECTATION.get(category, ("", ""))[0],
        "human_note": HUMAN_EXPECTATION.get(category, ("", ""))[1],
    }
    if sharp_dim is not None:
        entry["raw_sharpness"] = raw_sharp
        entry["noise_corrected"] = sharp_dim.details.get("noise_corrected", False)
    return entry


def _category_summary(entries: list[dict]) -> dict:
    return {
        "count": len(entries),
        "avg_overall": round(sum(e["overall"] for e in entries) / len(entries), 1),
        "avg_elapsed_ms": round(sum(e["elapsed_ms"] for e in entries) / len(entries), 1),
    }


def run_benchmark() -> dict:
    manifest_path = SAMPLES / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError("请先运行 tests/generate_samples.py")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dl_ready = is_dl_available()
    active_methods = list(METHODS) if dl_ready else ["traditional"]

    results = {
        "samples": [],
        "summary": {},
        "methods": active_methods,
        "dl_available": dl_ready,
    }

    for category, files in manifest["categories"].items():
        for rel in files:
            path = ROOT / rel
            for method in active_methods:
                report = analyze_image(str(path), method=method)
                entry = _sample_entry(category, rel, method, report)
                results["samples"].append(entry)
                results["summary"].setdefault(method, {})
                results["summary"][method].setdefault(category, {"entries": []})
                results["summary"][method][category]["entries"].append(entry)

    for method, cats in results["summary"].items():
        for cat, data in cats.items():
            data.update(_category_summary(data["entries"]))

    OUT.mkdir(parents=True, exist_ok=True)
    json_path = OUT / "benchmark_results.json"
    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    md_lines = [
        "# 验证证据 · 基准测试结果",
        "",
        "## 测试环境",
        "- 传统：OpenCV 四维度加权（清晰度 35% + 曝光 25% + 噪点 25% + 对比度 15%）",
        f"- 深度学习：{'pyiqa（cnniqa，CPU）' if dl_ready else '未安装，已跳过'}",
        "- 混合：传统综合分 × 0.5 + 深度学习分 × 0.5",
        "- 分析前最长边缩放至 1280px",
        "",
    ]

    # ── Category summary tables ───────────────────────────────────────────────
    for method in active_methods:
        label = METHOD_LABELS[method]
        md_lines.extend([
            f"## {label} · 分类汇总",
            "",
            "| 类别 | 样本数 | 平均综合分 | 平均耗时(ms) | 人工预期 |",
            "|------|--------|-----------|-------------|----------|",
        ])
        for cat, s in results["summary"][method].items():
            exp = HUMAN_EXPECTATION.get(cat, ("", ""))[0]
            md_lines.append(
                f"| {cat} | {s['count']} | {s['avg_overall']} | {s['avg_elapsed_ms']} | {exp} |"
            )
        md_lines.append("")

    # ── Cross-method comparison ───────────────────────────────────────────────
    if dl_ready and "traditional" in active_methods and "dl" in active_methods:
        md_lines.extend([
            "## 传统 vs 深度学习 · 综合分对比",
            "",
            "| 类别 | 传统均分 | 深度学习均分 | 混合均分 | 趋势一致性 |",
            "|------|---------|-------------|---------|-----------| ",
        ])
        trad_cats = results["summary"]["traditional"]
        for cat in trad_cats:
            t = results["summary"]["traditional"][cat]["avg_overall"]
            d = results["summary"]["dl"][cat]["avg_overall"]
            h = results["summary"]["hybrid"][cat]["avg_overall"]
            same_trend = "✅" if (t >= 60) == (d >= 60) else "⚠️ 分歧"
            md_lines.append(f"| {cat} | {t} | {d} | {h} | {same_trend} |")
        md_lines.append("")

    # ── Detailed per-sample results ───────────────────────────────────────────
    md_lines.extend(["", "## 详细结果", ""])
    for method in active_methods:
        label = METHOD_LABELS[method]
        md_lines.append(f"### 模式：{label}")
        md_lines.append("")
        for e in results["samples"]:
            if e["method"] != method:
                continue
            md_lines.append(f"#### {e['file']} ({e['category']})")
            md_lines.append(f"- 综合分: **{e['overall']}** ({e['grade']})")
            md_lines.append(f"- 耗时: {e['elapsed_ms']} ms")
            md_lines.append(f"- 维度: {e['dimensions']}")
            if e.get("traditional_score") is not None and e.get("dl_score") is not None:
                md_lines.append(
                    f"- 融合: 传统 {e['traditional_score']} + DL {e['dl_score']}"
                )
            md_lines.append(f"- 评价: {e['summary']}")
            md_lines.append("")

    # ── Counterexample deep analysis ──────────────────────────────────────────
    counter_entries = [
        e for e in results["samples"]
        if e["category"] == "counterexample" and e["method"] == "traditional"
    ]
    if counter_entries:
        md_lines.extend([
            "## 反例深度分析（传统算法）",
            "",
            "> 以下反例展示了传统 CV 画质评分算法的**固有局限性**。"
            "每个反例都代表一种常见的评分失准模式。",
            "",
        ])
        for c in counter_entries:
            fname = Path(c["file"]).name
            analysis = COUNTEREXAMPLE_ANALYSIS.get(fname, {})
            sharp_score = c["dimensions"].get("sharpness")
            raw_sharp = c.get("raw_sharpness", sharp_score)
            noise_score = c["dimensions"].get("noise")
            contrast_score = c["dimensions"].get("contrast")
            exposure_score = c["dimensions"].get("exposure")

            md_lines.extend([
                f"### 反例：`{c['file']}`",
                "",
                f"| 指标 | 值 |",
                f"|------|-----|",
                f"| 综合分 | **{c['overall']}** ({c['grade']}) |",
                f"| 清晰度（原始 Laplacian） | {raw_sharp} |",
                f"| 清晰度（校正后） | {sharp_score} |",
                f"| 噪点分 | {noise_score} |",
                f"| 曝光分 | {exposure_score} |",
                f"| 对比度分 | {contrast_score} |",
                "",
            ])

            if analysis:
                md_lines.extend([
                    f"**人工判断**：画质{analysis['human_quality']}——{analysis['human_reason']}",
                    "",
                    f"**预期失准点**：{analysis['expected_failure']}",
                    "",
                    f"**根因分析**：{analysis['root_cause']}",
                    "",
                ])

            # DL comparison if available
            if dl_ready:
                dl_c = next(
                    (e for e in results["samples"]
                     if e["file"] == c["file"] and e["method"] == "dl"),
                    None,
                )
                if dl_c:
                    md_lines.extend([
                        f"**深度学习模式对比**：综合分 **{dl_c['overall']}** — {dl_c['summary']}",
                        "",
                    ])

            md_lines.append("---")
            md_lines.append("")

    # ── Comparison analysis table ─────────────────────────────────────────────
    md_lines.extend([
        "## 评分结果 vs 人工判断对比",
        "",
        "| 类别 | 样本 | 综合分 | 清晰度 | 曝光 | 噪点 | 对比度 | 人工判断 | 一致？ |",
        "|------|------|--------|--------|------|------|--------|----------|--------|",
    ])
    for e in results["samples"]:
        if e["method"] != "traditional":
            continue
        dims = e["dimensions"]
        human = HUMAN_EXPECTATION.get(e["category"], ("", ""))[0]
        # Determine consistency
        if e["category"] == "clear":
            consistent = "✅" if e["overall"] >= 70 else "❌"
        elif e["category"] in ("blur", "noise"):
            consistent = "✅" if e["overall"] < 85 else "⚠️"
        elif e["category"] in ("overexpose", "underexpose"):
            consistent = "✅" if dims.get("exposure", 100) < 70 else "⚠️"
        elif e["category"] == "counterexample":
            consistent = "❌ 失准"
        else:
            consistent = "—"

        fname = Path(e["file"]).name
        md_lines.append(
            f"| {e['category']} | {fname} | {e['overall']} | "
            f"{dims.get('sharpness', '—')} | {dims.get('exposure', '—')} | "
            f"{dims.get('noise', '—')} | {dims.get('contrast', '—')} | "
            f"{human} | {consistent} |"
        )
    md_lines.append("")

    md_path = OUT / "benchmark_report.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    if not dl_ready:
        print("Note: 深度学习依赖未安装，仅运行传统模式。安装：pip install -r requirements-dl.txt")
    return results


if __name__ == "__main__":
    run_benchmark()
