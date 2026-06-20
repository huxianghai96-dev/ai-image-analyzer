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
    "counterexample": ("失准", "清晰度可能虚高（噪点被当作边缘），综合分与主观不符"),
    "formats": ("一致", "同内容不同格式分数应接近"),
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
        "- 传统：OpenCV 四维度加权",
        f"- 深度学习：{'pyiqa（cnniqa，CPU）' if dl_ready else '未安装，已跳过'}",
        "- 混合：传统综合分 × 0.5 + 深度学习分 × 0.5",
        "- 分析前最长边缩放至 1280px",
        "",
    ]

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

    if dl_ready and "traditional" in active_methods and "dl" in active_methods:
        md_lines.extend([
            "## 传统 vs 深度学习 · 综合分对比",
            "",
            "| 类别 | 传统均分 | 深度学习均分 | 混合均分 | 趋势一致性 |",
            "|------|---------|-------------|---------|-----------|",
        ])
        trad_cats = results["summary"]["traditional"]
        for cat in trad_cats:
            t = results["summary"]["traditional"][cat]["avg_overall"]
            d = results["summary"]["dl"][cat]["avg_overall"]
            h = results["summary"]["hybrid"][cat]["avg_overall"]
            same_trend = "✅" if (t >= 60) == (d >= 60) else "⚠️ 分歧"
            md_lines.append(f"| {cat} | {t} | {d} | {h} | {same_trend} |")
        md_lines.append("")

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

    counter = [
        e for e in results["samples"]
        if e["category"] == "counterexample" and e["method"] == "traditional"
    ]
    if counter:
        c = counter[0]
        sharp_score = c["dimensions"].get("sharpness")
        raw_sharp = c.get("raw_sharpness", sharp_score)
        md_lines.extend([
            "## 反例分析（传统算法）",
            "",
            f"样本 `{c['file']}`：强颗粒噪点图像（高 ISO 模拟）。",
            "",
            f"- 算法清晰度分（原始 Laplacian）: **{raw_sharp}**",
            f"- 算法清晰度分（噪点校正后）: **{sharp_score}**",
            f"- 噪点分: **{c['dimensions'].get('noise')}**",
            f"- 综合分: **{c['overall']}**",
            "- 人工判断: 画面颗粒重、细节被噪点掩盖，整体画质差",
            "",
        ])
        if dl_ready:
            dl_c = next(e for e in results["samples"] if e["category"] == "counterexample" and e["method"] == "dl")
            md_lines.extend([
                "### 反例在深度学习模式下的表现",
                f"- 深度学习综合分: **{dl_c['overall']}**",
                f"- 评价: {dl_c['summary']}",
                "",
            ])

    md_path = OUT / "benchmark_report.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    if not dl_ready:
        print("Note: 深度学习依赖未安装，仅运行传统模式。安装：pip install -r requirements-dl.txt")
    return results


if __name__ == "__main__":
    run_benchmark()
