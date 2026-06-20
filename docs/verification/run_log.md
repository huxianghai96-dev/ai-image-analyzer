# 运行日志摘要

> 由 `tests/run_benchmark.py` 于本地自动生成，用于验收「耗时控制」与「评分可复现」。

## 命令

```
pip install -r requirements.txt
python tests/generate_samples.py
python tests/run_benchmark.py
```

## 耗时结论

| 类别 | 平均耗时 (ms) | 是否 ≤ 1s |
|------|--------------|-----------|
| clear | ~67 | ✅ |
| blur | ~39 | ✅ |
| overexpose | ~42 | ✅ |
| underexpose | ~40 | ✅ |
| noise | ~48 | ✅ |
| large (12MP) | ~92 | ✅ |
| counterexample | ~45 | ✅ |
| formats | ~65 | ✅ |

**结论**：所有样本分析耗时均远低于 1000ms。12MP 大图因分析前缩放至 1280px，耗时约 90ms。

## 格式解码

| 格式 | 样本 | 结果 |
|------|------|------|
| JPEG | sample.jpg, clear_*.jpg | ✅ 解码成功 |
| PNG | sample.png | ✅ 解码成功 |
| WebP | sample.webp | ✅ 解码成功 |
| HEIC | sample.heic | ✅ 解码成功（pillow-heif） |

## 评分趋势 vs 人工

| 类别 | 算法趋势 | 人工判断 | 一致？ |
|------|----------|----------|--------|
| clear | ~93 分 | 清晰正常 | ✅ |
| blur | 88→69→63，清晰度 83→13 | 模糊加重 | ✅ |
| overexpose | 曝光分 0–40 | 过曝 | ✅ |
| underexpose | 曝光分 62–72，综合 ~75 | 偏暗 | ✅ 曝光维度偏低 |
| noise | 综合 89→80→69，噪点分 78→42 | 噪点加重 | ✅ |
| counterexample | 清晰度原始 100→校正 75，综合 73 | 画质差 | ❌ 原始清晰度失准（已分析） |

完整 JSON 数据：`benchmark_results.json`  
完整报告：`benchmark_report.md`
