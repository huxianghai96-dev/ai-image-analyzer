# 验证证据 · 基准测试结果

## 测试环境
- 传统：OpenCV 四维度加权
- 深度学习：pyiqa（cnniqa，CPU）
- 混合：传统综合分 × 0.5 + 深度学习分 × 0.5
- 分析前最长边缩放至 1280px

## 传统算法 · 分类汇总

| 类别 | 样本数 | 平均综合分 | 平均耗时(ms) | 人工预期 |
|------|--------|-----------|-------------|----------|
| clear | 2 | 93.2 | 82.7 | 高 |
| blur | 3 | 73.4 | 55.6 | 低 |
| overexpose | 2 | 75.0 | 50.0 | 低 |
| underexpose | 2 | 74.9 | 45.9 | 低 |
| noise | 3 | 79.5 | 55.7 | 低 |
| large | 1 | 88.8 | 115.4 | 中 |
| counterexample | 1 | 73.3 | 60.9 | 失准 |
| formats | 4 | 93.3 | 87.9 | 一致 |

## 深度学习 · 分类汇总

| 类别 | 样本数 | 平均综合分 | 平均耗时(ms) | 人工预期 |
|------|--------|-----------|-------------|----------|
| clear | 2 | 48.4 | 423.4 | 高 |
| blur | 3 | 35.7 | 252.4 | 低 |
| overexpose | 2 | 51.8 | 237.6 | 低 |
| underexpose | 2 | 10.3 | 234.4 | 低 |
| noise | 3 | 58.8 | 241.4 | 低 |
| large | 1 | 49.3 | 305.4 | 中 |
| counterexample | 1 | 61.4 | 266.6 | 失准 |
| formats | 4 | 47.8 | 271.1 | 一致 |

## 混合模式 · 分类汇总

| 类别 | 样本数 | 平均综合分 | 平均耗时(ms) | 人工预期 |
|------|--------|-----------|-------------|----------|
| clear | 2 | 70.8 | 346.6 | 高 |
| blur | 3 | 54.5 | 276.6 | 低 |
| overexpose | 2 | 63.4 | 269.6 | 低 |
| underexpose | 2 | 42.6 | 265.4 | 低 |
| noise | 3 | 69.1 | 276.6 | 低 |
| large | 1 | 69.1 | 345.2 | 中 |
| counterexample | 1 | 67.3 | 274.8 | 失准 |
| formats | 4 | 70.5 | 303.7 | 一致 |

## 传统 vs 深度学习 · 综合分对比

| 类别 | 传统均分 | 深度学习均分 | 混合均分 | 趋势一致性 |
|------|---------|-------------|---------|-----------|
| clear | 93.2 | 48.4 | 70.8 | ⚠️ 分歧 |
| blur | 73.4 | 35.7 | 54.5 | ⚠️ 分歧 |
| overexpose | 75.0 | 51.8 | 63.4 | ⚠️ 分歧 |
| underexpose | 74.9 | 10.3 | 42.6 | ⚠️ 分歧 |
| noise | 79.5 | 58.8 | 69.1 | ⚠️ 分歧 |
| large | 88.8 | 49.3 | 69.1 | ⚠️ 分歧 |
| counterexample | 73.3 | 61.4 | 67.3 | ✅ |
| formats | 93.3 | 47.8 | 70.5 | ⚠️ 分歧 |


## 详细结果

### 模式：传统算法

#### test_samples\clear\clear_1.jpg (clear)
- 综合分: **93.2** (A 优秀)
- 耗时: 98.6 ms
- 维度: {'sharpness': 99.1, 'exposure': 96.0, 'noise': 95.5, 'contrast': 71.2}
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好。

#### test_samples\clear\clear_2.jpg (clear)
- 综合分: **93.2** (A 优秀)
- 耗时: 66.7 ms
- 维度: {'sharpness': 99.1, 'exposure': 96.0, 'noise': 95.5, 'contrast': 71.2}
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好。

#### test_samples\blur\blur_k5.jpg (blur)
- 综合分: **88.0** (B 良好)
- 耗时: 58.4 ms
- 维度: {'sharpness': 83.3, 'exposure': 96.0, 'noise': 97.0, 'contrast': 70.6}
- 评价: 清晰度：基本清晰；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好。

#### test_samples\blur\blur_k15.jpg (blur)
- 综合分: **68.9** (C 一般)
- 耗时: 54.8 ms
- 维度: {'sharpness': 28.8, 'exposure': 96.0, 'noise': 97.2, 'contrast': 70.0}
- 评价: 清晰度：明显模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度一般。

#### test_samples\blur\blur_k31.jpg (blur)
- 综合分: **63.4** (C 一般)
- 耗时: 53.7 ms
- 维度: {'sharpness': 13.3, 'exposure': 96.0, 'noise': 97.3, 'contrast': 69.5}
- 评价: 清晰度：严重模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度一般。

#### test_samples\overexpose\over_1.jpg (overexpose)
- 综合分: **80.6** (B 良好)
- 耗时: 49.1 ms
- 维度: {'sharpness': 100.0, 'exposure': 40.4, 'noise': 95.4, 'contrast': 78.0}
- 评价: 清晰度：非常清晰；曝光：过曝；噪点：噪点极低；对比度：对比度良好。

#### test_samples\overexpose\over_2.jpg (overexpose)
- 综合分: **69.4** (C 一般)
- 耗时: 50.8 ms
- 维度: {'sharpness': 100.0, 'exposure': 0.0, 'noise': 96.1, 'contrast': 68.9}
- 评价: 清晰度：非常清晰；曝光：过曝；噪点：噪点极低；对比度：对比度一般。

#### test_samples\underexpose\under_1.jpg (underexpose)
- 综合分: **70.6** (C 一般)
- 耗时: 45.2 ms
- 维度: {'sharpness': 75.2, 'exposure': 62.3, 'noise': 97.0, 'contrast': 29.4}
- 评价: 清晰度：基本清晰；曝光：整体偏暗；噪点：噪点极低；对比度：对比度偏低。

#### test_samples\underexpose\under_2.jpg (underexpose)
- 综合分: **79.2** (B 良好)
- 耗时: 46.6 ms
- 维度: {'sharpness': 88.1, 'exposure': 71.9, 'noise': 96.7, 'contrast': 41.5}
- 评价: 清晰度：清晰；曝光：整体偏暗；噪点：噪点极低；对比度：对比度一般。

#### test_samples\noise\noise_s15.jpg (noise)
- 综合分: **89.3** (B 良好)
- 耗时: 50.6 ms
- 维度: {'sharpness': 100.0, 'exposure': 96.2, 'noise': 77.8, 'contrast': 71.7}
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点轻微；对比度：对比度良好。

#### test_samples\noise\noise_s30.jpg (noise)
- 综合分: **80.4** (B 良好)
- 耗时: 59.3 ms
- 维度: {'sharpness': 87.0, 'exposure': 96.2, 'noise': 59.6, 'contrast': 73.0}
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点中等；对比度：对比度良好。

#### test_samples\noise\noise_s50.jpg (noise)
- 综合分: **68.7** (C 一般)
- 耗时: 57.2 ms
- 维度: {'sharpness': 65.5, 'exposure': 96.3, 'noise': 41.7, 'contrast': 75.1}
- 评价: 清晰度：非常清晰（噪点干扰已校正）；曝光：曝光正常；噪点：噪点明显；对比度：对比度良好。

#### test_samples\large\large_12mp.jpg (large)
- 综合分: **88.8** (B 良好)
- 耗时: 115.4 ms
- 维度: {'sharpness': 100.0, 'exposure': 96.0, 'noise': 76.8, 'contrast': 70.7}
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点轻微；对比度：对比度良好。

#### test_samples\counterexample\noise_masquerade_sharp.jpg (counterexample)
- 综合分: **73.3** (C 一般)
- 耗时: 60.9 ms
- 维度: {'sharpness': 74.8, 'exposure': 96.2, 'noise': 47.7, 'contrast': 74.0}
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点明显；对比度：对比度良好。

#### test_samples\formats\sample.png (formats)
- 综合分: **93.3** (A 优秀)
- 耗时: 91.0 ms
- 维度: {'sharpness': 99.0, 'exposure': 96.0, 'noise': 95.7, 'contrast': 71.2}
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好。

#### test_samples\formats\sample.webp (formats)
- 综合分: **93.3** (A 优秀)
- 耗时: 70.4 ms
- 维度: {'sharpness': 99.0, 'exposure': 96.0, 'noise': 95.7, 'contrast': 71.2}
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好。

#### test_samples\formats\sample.jpg (formats)
- 综合分: **93.4** (A 优秀)
- 耗时: 58.5 ms
- 维度: {'sharpness': 99.4, 'exposure': 96.0, 'noise': 95.9, 'contrast': 71.2}
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好。

#### test_samples\formats\sample.heic (formats)
- 综合分: **93.1** (A 优秀)
- 耗时: 131.7 ms
- 维度: {'sharpness': 98.2, 'exposure': 96.0, 'noise': 96.2, 'contrast': 71.2}
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好。

### 模式：深度学习

#### test_samples\clear\clear_1.jpg (clear)
- 综合分: **48.4** (D 较差)
- 耗时: 545.4 ms
- 维度: {'deep_learning': 48.4}
- 评价: 深度学习画质：画质偏差。

#### test_samples\clear\clear_2.jpg (clear)
- 综合分: **48.4** (D 较差)
- 耗时: 301.4 ms
- 维度: {'deep_learning': 48.4}
- 评价: 深度学习画质：画质偏差。

#### test_samples\blur\blur_k5.jpg (blur)
- 综合分: **37.7** (E 很差)
- 耗时: 268.8 ms
- 维度: {'deep_learning': 37.7}
- 评价: 深度学习画质：画质较差。

#### test_samples\blur\blur_k15.jpg (blur)
- 综合分: **34.5** (E 很差)
- 耗时: 254.6 ms
- 维度: {'deep_learning': 34.5}
- 评价: 深度学习画质：画质较差。

#### test_samples\blur\blur_k31.jpg (blur)
- 综合分: **34.8** (E 很差)
- 耗时: 233.8 ms
- 维度: {'deep_learning': 34.8}
- 评价: 深度学习画质：画质较差。

#### test_samples\overexpose\over_1.jpg (overexpose)
- 综合分: **51.0** (D 较差)
- 耗时: 238.9 ms
- 维度: {'deep_learning': 51.0}
- 评价: 深度学习画质：画质偏差。

#### test_samples\overexpose\over_2.jpg (overexpose)
- 综合分: **52.6** (D 较差)
- 耗时: 236.3 ms
- 维度: {'deep_learning': 52.6}
- 评价: 深度学习画质：画质偏差。

#### test_samples\underexpose\under_1.jpg (underexpose)
- 综合分: **0.0** (E 很差)
- 耗时: 233.8 ms
- 维度: {'deep_learning': 0.0}
- 评价: 深度学习画质：画质较差。

#### test_samples\underexpose\under_2.jpg (underexpose)
- 综合分: **20.7** (E 很差)
- 耗时: 234.9 ms
- 维度: {'deep_learning': 20.7}
- 评价: 深度学习画质：画质较差。

#### test_samples\noise\noise_s15.jpg (noise)
- 综合分: **53.1** (D 较差)
- 耗时: 234.5 ms
- 维度: {'deep_learning': 53.1}
- 评价: 深度学习画质：画质偏差。

#### test_samples\noise\noise_s30.jpg (noise)
- 综合分: **58.3** (D 较差)
- 耗时: 238.6 ms
- 维度: {'deep_learning': 58.3}
- 评价: 深度学习画质：画质一般。

#### test_samples\noise\noise_s50.jpg (noise)
- 综合分: **64.9** (C 一般)
- 耗时: 251.0 ms
- 维度: {'deep_learning': 64.9}
- 评价: 深度学习画质：画质一般。

#### test_samples\large\large_12mp.jpg (large)
- 综合分: **49.3** (D 较差)
- 耗时: 305.4 ms
- 维度: {'deep_learning': 49.3}
- 评价: 深度学习画质：画质偏差。

#### test_samples\counterexample\noise_masquerade_sharp.jpg (counterexample)
- 综合分: **61.4** (C 一般)
- 耗时: 266.6 ms
- 维度: {'deep_learning': 61.4}
- 评价: 深度学习画质：画质一般。

#### test_samples\formats\sample.png (formats)
- 综合分: **47.7** (D 较差)
- 耗时: 267.4 ms
- 维度: {'deep_learning': 47.7}
- 评价: 深度学习画质：画质偏差。

#### test_samples\formats\sample.webp (formats)
- 综合分: **47.7** (D 较差)
- 耗时: 268.4 ms
- 维度: {'deep_learning': 47.7}
- 评价: 深度学习画质：画质偏差。

#### test_samples\formats\sample.jpg (formats)
- 综合分: **48.8** (D 较差)
- 耗时: 246.3 ms
- 维度: {'deep_learning': 48.8}
- 评价: 深度学习画质：画质偏差。

#### test_samples\formats\sample.heic (formats)
- 综合分: **47.0** (D 较差)
- 耗时: 302.5 ms
- 维度: {'deep_learning': 47.0}
- 评价: 深度学习画质：画质偏差。

### 模式：混合模式

#### test_samples\clear\clear_1.jpg (clear)
- 综合分: **70.8** (C 一般)
- 耗时: 379.9 ms
- 维度: {'sharpness': 99.1, 'exposure': 96.0, 'noise': 95.5, 'contrast': 71.2, 'deep_learning': 48.4}
- 融合: 传统 93.24000000000001 + DL 48.4
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质偏差。

#### test_samples\clear\clear_2.jpg (clear)
- 综合分: **70.8** (C 一般)
- 耗时: 313.3 ms
- 维度: {'sharpness': 99.1, 'exposure': 96.0, 'noise': 95.5, 'contrast': 71.2, 'deep_learning': 48.4}
- 融合: 传统 93.24000000000001 + DL 48.4
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质偏差。

#### test_samples\blur\blur_k5.jpg (blur)
- 综合分: **62.8** (C 一般)
- 耗时: 301.5 ms
- 维度: {'sharpness': 83.3, 'exposure': 96.0, 'noise': 97.0, 'contrast': 70.6, 'deep_learning': 37.7}
- 融合: 传统 87.995 + DL 37.7
- 评价: 清晰度：基本清晰；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质较差。

#### test_samples\blur\blur_k15.jpg (blur)
- 综合分: **51.7** (D 较差)
- 耗时: 266.0 ms
- 维度: {'sharpness': 28.8, 'exposure': 96.0, 'noise': 97.2, 'contrast': 70.0, 'deep_learning': 34.5}
- 融合: 传统 68.88 + DL 34.5
- 评价: 清晰度：明显模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度一般；深度学习画质：画质较差。

#### test_samples\blur\blur_k31.jpg (blur)
- 综合分: **49.1** (D 较差)
- 耗时: 262.2 ms
- 维度: {'sharpness': 13.3, 'exposure': 96.0, 'noise': 97.3, 'contrast': 69.5, 'deep_learning': 34.8}
- 融合: 传统 63.405 + DL 34.8
- 评价: 清晰度：严重模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度一般；深度学习画质：画质较差。

#### test_samples\overexpose\over_1.jpg (overexpose)
- 综合分: **65.8** (C 一般)
- 耗时: 274.6 ms
- 维度: {'sharpness': 100.0, 'exposure': 40.4, 'noise': 95.4, 'contrast': 78.0, 'deep_learning': 51.0}
- 融合: 传统 80.65 + DL 51.0
- 评价: 清晰度：非常清晰；曝光：过曝；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质偏差。

#### test_samples\overexpose\over_2.jpg (overexpose)
- 综合分: **61.0** (C 一般)
- 耗时: 264.6 ms
- 维度: {'sharpness': 100.0, 'exposure': 0.0, 'noise': 96.1, 'contrast': 68.9, 'deep_learning': 52.6}
- 融合: 传统 69.36 + DL 52.6
- 评价: 清晰度：非常清晰；曝光：过曝；噪点：噪点极低；对比度：对比度一般；深度学习画质：画质偏差。

#### test_samples\underexpose\under_1.jpg (underexpose)
- 综合分: **35.3** (E 很差)
- 耗时: 268.7 ms
- 维度: {'sharpness': 75.2, 'exposure': 62.3, 'noise': 97.0, 'contrast': 29.4, 'deep_learning': 0.0}
- 融合: 传统 70.55499999999999 + DL 0.0
- 评价: 清晰度：基本清晰；曝光：整体偏暗；噪点：噪点极低；对比度：对比度偏低；深度学习画质：画质较差。

#### test_samples\underexpose\under_2.jpg (underexpose)
- 综合分: **50.0** (D 较差)
- 耗时: 262.0 ms
- 维度: {'sharpness': 88.1, 'exposure': 71.9, 'noise': 96.7, 'contrast': 41.5, 'deep_learning': 20.7}
- 融合: 传统 79.21 + DL 20.7
- 评价: 清晰度：清晰；曝光：整体偏暗；噪点：噪点极低；对比度：对比度一般；深度学习画质：画质较差。

#### test_samples\noise\noise_s15.jpg (noise)
- 综合分: **71.2** (C 一般)
- 耗时: 273.2 ms
- 维度: {'sharpness': 100.0, 'exposure': 96.2, 'noise': 77.8, 'contrast': 71.7, 'deep_learning': 53.1}
- 融合: 传统 89.255 + DL 53.1
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点轻微；对比度：对比度良好；深度学习画质：画质偏差。

#### test_samples\noise\noise_s30.jpg (noise)
- 综合分: **69.3** (C 一般)
- 耗时: 275.0 ms
- 维度: {'sharpness': 87.0, 'exposure': 96.2, 'noise': 59.6, 'contrast': 73.0, 'deep_learning': 58.3}
- 融合: 传统 80.35000000000001 + DL 58.3
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点中等；对比度：对比度良好；深度学习画质：画质一般。

#### test_samples\noise\noise_s50.jpg (noise)
- 综合分: **66.8** (C 一般)
- 耗时: 281.7 ms
- 维度: {'sharpness': 65.5, 'exposure': 96.3, 'noise': 41.7, 'contrast': 75.1, 'deep_learning': 64.9}
- 融合: 传统 68.69 + DL 64.9
- 评价: 清晰度：非常清晰（噪点干扰已校正）；曝光：曝光正常；噪点：噪点明显；对比度：对比度良好；深度学习画质：画质一般。

#### test_samples\large\large_12mp.jpg (large)
- 综合分: **69.1** (C 一般)
- 耗时: 345.2 ms
- 维度: {'sharpness': 100.0, 'exposure': 96.0, 'noise': 76.8, 'contrast': 70.7, 'deep_learning': 49.3}
- 融合: 传统 88.805 + DL 49.3
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点轻微；对比度：对比度良好；深度学习画质：画质偏差。

#### test_samples\counterexample\noise_masquerade_sharp.jpg (counterexample)
- 综合分: **67.3** (C 一般)
- 耗时: 274.8 ms
- 维度: {'sharpness': 74.8, 'exposure': 96.2, 'noise': 47.7, 'contrast': 74.0, 'deep_learning': 61.4}
- 融合: 传统 73.255 + DL 61.4
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点明显；对比度：对比度良好；深度学习画质：画质一般。

#### test_samples\formats\sample.png (formats)
- 综合分: **70.5** (C 一般)
- 耗时: 293.5 ms
- 维度: {'sharpness': 99.0, 'exposure': 96.0, 'noise': 95.7, 'contrast': 71.2, 'deep_learning': 47.7}
- 融合: 传统 93.255 + DL 47.7
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质偏差。

#### test_samples\formats\sample.webp (formats)
- 综合分: **70.5** (C 一般)
- 耗时: 304.9 ms
- 维度: {'sharpness': 99.0, 'exposure': 96.0, 'noise': 95.7, 'contrast': 71.2, 'deep_learning': 47.7}
- 融合: 传统 93.255 + DL 47.7
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质偏差。

#### test_samples\formats\sample.jpg (formats)
- 综合分: **71.1** (C 一般)
- 耗时: 296.1 ms
- 维度: {'sharpness': 99.4, 'exposure': 96.0, 'noise': 95.9, 'contrast': 71.2, 'deep_learning': 48.8}
- 融合: 传统 93.445 + DL 48.8
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质偏差。

#### test_samples\formats\sample.heic (formats)
- 综合分: **70.0** (C 一般)
- 耗时: 320.4 ms
- 维度: {'sharpness': 98.2, 'exposure': 96.0, 'noise': 96.2, 'contrast': 71.2, 'deep_learning': 47.0}
- 融合: 传统 93.1 + DL 47.0
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质偏差。

## 反例分析（传统算法）

样本 `test_samples\counterexample\noise_masquerade_sharp.jpg`：强颗粒噪点图像（高 ISO 模拟）。

- 算法清晰度分（原始 Laplacian）: **100.0**
- 算法清晰度分（噪点校正后）: **74.8**
- 噪点分: **47.7**
- 综合分: **73.3**
- 人工判断: 画面颗粒重、细节被噪点掩盖，整体画质差

### 反例在深度学习模式下的表现
- 深度学习综合分: **61.4**
- 评价: 深度学习画质：画质一般。
