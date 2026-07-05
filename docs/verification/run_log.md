# 运行日志摘要

> 由 `tests/run_benchmark.py` 于本地自动生成，用于验收「耗时控制」与「评分可复现」。

## 命令

```
pip install -r requirements.txt
python tests/generate_samples.py
python tests/run_benchmark.py
```

## 测试样本

| 类别 | 样本数 | 描述 |
|------|--------|------|
| clear | 3 | 清晰纹理 / 清晰场景 / 轻度锐化 |
| blur | 3 | Gaussian k=5/15/31 逐级模糊 |
| overexpose | 3 | gain=1.4/1.8/2.2 逐级过曝 |
| underexpose | 3 | gain=0.25/0.4/0.55 逐级欠曝 |
| noise | 3 | sigma=15/30/50 逐级噪点 |
| large | 1 | 4000×3000 (12MP) 性能测试 |
| counterexample | 3 | 噪点伪装清晰 / 过度锐化 / 雾天低对比 |
| formats | 4 | PNG / WebP / JPEG / HEIC 同内容 |

总计 **23 张**合成样本。

## 耗时结论

| 类别 | 平均耗时 (ms) | 是否 ≤ 1s |
|------|--------------|-----------| 
| clear | ~82 | ✅ |
| blur | ~66 | ✅ |
| overexpose | ~70 | ✅ |
| underexpose | ~65 | ✅ |
| noise | ~79 | ✅ |
| large (12MP) | ~122 | ✅ |
| counterexample | ~72 | ✅ |
| formats | ~107 | ✅ |

**结论**：所有样本分析耗时均远低于 1000ms。12MP 大图因分析前缩放至 1280px，耗时约 122ms。

## 格式解码

| 格式 | 样本 | 结果 |
|------|------|------|
| JPEG | *.jpg | ✅ 解码成功 |
| PNG | sample.png | ✅ 解码成功 |
| WebP | sample.webp | ✅ 解码成功 |
| HEIC | sample.heic | ✅ 解码成功（pillow-heif） |

## 反例分析摘要

| 反例 | 核心问题 | 失准维度 | 根因 |
|------|----------|----------|------|
| noise_masquerade_sharp | 颗粒噪点被 Laplacian 当作清晰边缘 | 清晰度虚高 | Laplacian 无法区分纹理与噪点高频 |
| over_sharpened_halo | USM 锐化产生光晕但 Laplacian 更高 | 清晰度虚高 | Laplacian 直接响应锐化增强的边缘 |
| foggy_low_contrast | 雾天亮度正常但画面发灰 | 曝光偏高但对比度低 | 全局均值曝光无法检测信息量缺失 |

详见 `benchmark_report.md` 中的反例深度分析章节。

## 评分趋势 vs 人工

| 类别 | 算法趋势 | 人工判断 | 一致？ |
|------|----------|----------|--------|
| clear | 综合分高（≥80） | 清晰正常 | ✅ |
| blur | 综合分随 k 增大下降 | 模糊加重 | ✅ |
| overexpose | 曝光分极低 | 过曝 | ✅ |
| underexpose | 曝光分偏低 | 偏暗 | ✅ |
| noise | 噪点分随 sigma 下降 | 噪点加重 | ✅ |
| counterexample | 至少 1 维度失准 | 画质差 | ❌ 已分析原因 |

完整 JSON 数据：`benchmark_results.json`  
完整报告：`benchmark_report.md`
