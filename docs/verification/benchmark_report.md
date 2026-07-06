# 验证证据 · 基准测试结果

## 测试环境
- 传统：OpenCV 四维度加权（清晰度 35% + 曝光 25% + 噪点 25% + 对比度 15%）
- 深度学习：pyiqa（cnniqa，CPU）
- 混合：传统综合分 × 0.5 + 深度学习分 × 0.5
- 分析前最长边缩放至 1280px

## 传统算法 · 分类汇总

| 类别 | 样本数 | 平均综合分 | 平均耗时(ms) | 人工预期 |
|------|--------|-----------|-------------|----------|
| clear | 3 | 83.1 | 73.3 | 高 |
| blur | 3 | 53.6 | 57.9 | 低 |
| overexpose | 3 | 75.7 | 59.9 | 低 |
| underexpose | 3 | 46.5 | 58.2 | 低 |
| noise | 3 | 62.5 | 68.7 | 低 |
| large | 1 | 81.7 | 106.0 | 中 |
| counterexample | 3 | 60.9 | 63.8 | 失准 |
| formats | 4 | 84.2 | 93.6 | 一致 |

## 深度学习 · 分类汇总

| 类别 | 样本数 | 平均综合分 | 平均耗时(ms) | 人工预期 |
|------|--------|-----------|-------------|----------|
| clear | 3 | 52.1 | 304.5 | 高 |
| blur | 3 | 37.9 | 224.7 | 低 |
| overexpose | 3 | 50.8 | 236.9 | 低 |
| underexpose | 3 | 27.1 | 232.5 | 低 |
| noise | 3 | 62.7 | 238.9 | 低 |
| large | 1 | 52.5 | 275.9 | 中 |
| counterexample | 3 | 60.5 | 230.7 | 失准 |
| formats | 4 | 51.8 | 259.4 | 一致 |

## 混合模式 · 分类汇总

| 类别 | 样本数 | 平均综合分 | 平均耗时(ms) | 人工预期 |
|------|--------|-----------|-------------|----------|
| clear | 3 | 67.6 | 324.3 | 高 |
| blur | 3 | 45.7 | 271.1 | 低 |
| overexpose | 3 | 63.3 | 288.3 | 低 |
| underexpose | 3 | 36.8 | 286.0 | 低 |
| noise | 3 | 62.6 | 284.7 | 低 |
| large | 1 | 67.1 | 345.5 | 中 |
| counterexample | 3 | 60.7 | 290.3 | 失准 |
| formats | 4 | 68.0 | 313.8 | 一致 |

## 传统 vs 深度学习 · 综合分对比

| 类别 | 传统均分 | 深度学习均分 | 混合均分 | 趋势一致性 |
|------|---------|-------------|---------|-----------| 
| clear | 83.1 | 52.1 | 67.6 | ⚠️ 分歧 |
| blur | 53.6 | 37.9 | 45.7 | ✅ |
| overexpose | 75.7 | 50.8 | 63.3 | ⚠️ 分歧 |
| underexpose | 46.5 | 27.1 | 36.8 | ✅ |
| noise | 62.5 | 62.7 | 62.6 | ✅ |
| large | 81.7 | 52.5 | 67.1 | ⚠️ 分歧 |
| counterexample | 60.9 | 60.5 | 60.7 | ✅ |
| formats | 84.2 | 51.8 | 68.0 | ⚠️ 分歧 |


## 详细结果

### 模式：传统算法

#### test_samples\clear\clear_texture.jpg (clear)
- 综合分: **79.0** (B 良好)
- 耗时: 73.0 ms
- 维度: {'sharpness': 78.8, 'exposure': 96.0, 'noise': 68.7, 'contrast': 71.2}
- 评价: 清晰度：非常清晰 (已校正噪点)；曝光：曝光正常；噪点：噪点中等；对比度：对比度良好。

#### test_samples\clear\clear_scene.jpg (clear)
- 综合分: **84.8** (B 良好)
- 耗时: 74.2 ms
- 维度: {'sharpness': 75.5, 'exposure': 95.9, 'noise': 95.3, 'contrast': 70.7}
- 评价: 清晰度：基本清晰；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好。

#### test_samples\clear\clear_sharp.jpg (clear)
- 综合分: **85.6** (B 良好)
- 耗时: 72.8 ms
- 维度: {'sharpness': 78.7, 'exposure': 95.9, 'noise': 93.8, 'contrast': 70.8}
- 评价: 清晰度：基本清晰；曝光：曝光正常；噪点：噪点轻微；对比度：对比度良好。

#### test_samples\blur\blur_k5.jpg (blur)
- 综合分: **64.2** (C 一般)
- 耗时: 62.8 ms
- 维度: {'sharpness': 27.3, 'exposure': 95.9, 'noise': 98.0, 'contrast': 70.6}
- 评价: 清晰度：严重模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好。

#### test_samples\blur\blur_k15.jpg (blur)
- 综合分: **49.0** (D 较差)
- 耗时: 58.2 ms
- 维度: {'sharpness': 5.3, 'exposure': 95.9, 'noise': 98.8, 'contrast': 70.5}
- 评价: 清晰度：严重模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好。

#### test_samples\blur\blur_k31.jpg (blur)
- 综合分: **47.5** (D 较差)
- 耗时: 52.6 ms
- 维度: {'sharpness': 3.0, 'exposure': 95.8, 'noise': 99.4, 'contrast': 70.4}
- 评价: 清晰度：严重模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好。

#### test_samples\overexpose\over_1_g1.4.jpg (overexpose)
- 综合分: **84.1** (B 良好)
- 耗时: 59.6 ms
- 维度: {'sharpness': 78.9, 'exposure': 82.7, 'noise': 95.8, 'contrast': 79.1}
- 评价: 清晰度：基本清晰；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好。

#### test_samples\overexpose\over_2_g1.8.jpg (overexpose)
- 综合分: **78.6** (B 良好)
- 耗时: 58.7 ms
- 维度: {'sharpness': 77.8, 'exposure': 67.2, 'noise': 96.5, 'contrast': 75.3}
- 评价: 清晰度：基本清晰；曝光：整体偏亮；噪点：噪点极低；对比度：对比度良好。

#### test_samples\overexpose\over_3_g2.2.jpg (overexpose)
- 综合分: **64.4** (C 一般)
- 耗时: 61.3 ms
- 维度: {'sharpness': 78.6, 'exposure': 43.7, 'noise': 97.4, 'contrast': 63.1}
- 评价: 清晰度：基本清晰；曝光：过曝；噪点：噪点极低；对比度：对比度一般。

#### test_samples\underexpose\under_1_g0.25.jpg (underexpose)
- 综合分: **26.9** (E 很差)
- 耗时: 55.2 ms
- 维度: {'sharpness': 13.0, 'exposure': 53.8, 'noise': 95.2, 'contrast': 20.6}
- 评价: 清晰度：严重模糊；曝光：整体偏暗；噪点：噪点极低；对比度：对比度偏低。

#### test_samples\underexpose\under_2_g0.4.jpg (underexpose)
- 综合分: **48.3** (D 较差)
- 耗时: 59.2 ms
- 维度: {'sharpness': 31.5, 'exposure': 62.2, 'noise': 95.7, 'contrast': 32.9}
- 评价: 清晰度：明显模糊；曝光：整体偏暗；噪点：噪点极低；对比度：对比度偏低。

#### test_samples\underexpose\under_3_g0.55.jpg (underexpose)
- 综合分: **64.3** (C 一般)
- 耗时: 60.2 ms
- 维度: {'sharpness': 46.4, 'exposure': 70.5, 'noise': 95.8, 'contrast': 44.0}
- 评价: 清晰度：明显模糊；曝光：整体偏暗；噪点：噪点极低；对比度：对比度一般。

#### test_samples\noise\noise_s15.jpg (noise)
- 综合分: **84.8** (B 良好)
- 耗时: 69.7 ms
- 维度: {'sharpness': 89.7, 'exposure': 95.6, 'noise': 75.1, 'contrast': 71.2}
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点中等；对比度：对比度良好。

#### test_samples\noise\noise_s30.jpg (noise)
- 综合分: **64.4** (C 一般)
- 耗时: 64.4 ms
- 维度: {'sharpness': 56.4, 'exposure': 95.6, 'noise': 57.3, 'contrast': 72.5}
- 评价: 清晰度：假性清晰(严重噪点)；曝光：曝光正常；噪点：噪点明显；对比度：对比度良好。

#### test_samples\noise\noise_s50.jpg (noise)
- 综合分: **38.2** (E 很差)
- 耗时: 72.1 ms
- 维度: {'sharpness': 26.7, 'exposure': 95.7, 'noise': 38.2, 'contrast': 74.4}
- 评价: 清晰度：假性清晰(严重噪点)；曝光：曝光正常；噪点：噪点明显；对比度：对比度良好。

#### test_samples\large\large_12mp.jpg (large)
- 综合分: **81.7** (B 良好)
- 耗时: 106.0 ms
- 维度: {'sharpness': 65.1, 'exposure': 95.6, 'noise': 97.6, 'contrast': 70.8}
- 评价: 清晰度：轻度模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好。

#### test_samples\counterexample\noise_masquerade_sharp.jpg (counterexample)
- 综合分: **48.3** (D 较差)
- 耗时: 70.8 ms
- 维度: {'sharpness': 33.2, 'exposure': 96.2, 'noise': 47.4, 'contrast': 74.0}
- 评价: 清晰度：假性清晰(严重噪点)；曝光：曝光正常；噪点：噪点明显；对比度：对比度良好。

#### test_samples\counterexample\over_sharpened_halo.jpg (counterexample)
- 综合分: **88.7** (B 良好)
- 耗时: 62.4 ms
- 维度: {'sharpness': 94.5, 'exposure': 95.9, 'noise': 84.0, 'contrast': 71.3}
- 评价: 清晰度：清晰；曝光：曝光正常；噪点：噪点轻微；对比度：对比度良好。

#### test_samples\counterexample\foggy_low_contrast.jpg (counterexample)
- 综合分: **45.6** (D 较差)
- 耗时: 58.3 ms
- 维度: {'sharpness': 25.4, 'exposure': 65.7, 'noise': 99.1, 'contrast': 28.8}
- 评价: 清晰度：严重模糊；曝光：整体偏亮；噪点：噪点极低；对比度：对比度偏低。

#### test_samples\formats\sample.png (formats)
- 综合分: **84.5** (B 良好)
- 耗时: 86.6 ms
- 维度: {'sharpness': 74.2, 'exposure': 95.9, 'noise': 95.6, 'contrast': 70.7}
- 评价: 清晰度：轻度模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好。

#### test_samples\formats\sample.webp (formats)
- 综合分: **84.5** (B 良好)
- 耗时: 94.8 ms
- 维度: {'sharpness': 74.2, 'exposure': 95.9, 'noise': 95.6, 'contrast': 70.7}
- 评价: 清晰度：轻度模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好。

#### test_samples\formats\sample.jpg (formats)
- 综合分: **84.3** (B 良好)
- 耗时: 67.2 ms
- 维度: {'sharpness': 73.5, 'exposure': 95.9, 'noise': 95.8, 'contrast': 70.7}
- 评价: 清晰度：轻度模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好。

#### test_samples\formats\sample.heic (formats)
- 综合分: **83.5** (B 良好)
- 耗时: 125.7 ms
- 维度: {'sharpness': 71.0, 'exposure': 95.9, 'noise': 96.1, 'contrast': 70.7}
- 评价: 清晰度：轻度模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好。

### 模式：深度学习

#### test_samples\clear\clear_texture.jpg (clear)
- 综合分: **48.4** (D 较差)
- 耗时: 374.9 ms
- 维度: {'deep_learning': 48.4}
- 评价: 深度学习画质：画质偏差。

#### test_samples\clear\clear_scene.jpg (clear)
- 综合分: **51.5** (D 较差)
- 耗时: 282.1 ms
- 维度: {'deep_learning': 51.5}
- 评价: 深度学习画质：画质偏差。

#### test_samples\clear\clear_sharp.jpg (clear)
- 综合分: **56.3** (D 较差)
- 耗时: 256.6 ms
- 维度: {'deep_learning': 56.3}
- 评价: 深度学习画质：画质一般。

#### test_samples\blur\blur_k5.jpg (blur)
- 综合分: **36.6** (E 很差)
- 耗时: 222.6 ms
- 维度: {'deep_learning': 36.6}
- 评价: 深度学习画质：画质较差。

#### test_samples\blur\blur_k15.jpg (blur)
- 综合分: **36.6** (E 很差)
- 耗时: 225.0 ms
- 维度: {'deep_learning': 36.6}
- 评价: 深度学习画质：画质较差。

#### test_samples\blur\blur_k31.jpg (blur)
- 综合分: **40.6** (D 较差)
- 耗时: 226.4 ms
- 维度: {'deep_learning': 40.6}
- 评价: 深度学习画质：画质偏差。

#### test_samples\overexpose\over_1_g1.4.jpg (overexpose)
- 综合分: **53.6** (D 较差)
- 耗时: 242.8 ms
- 维度: {'deep_learning': 53.6}
- 评价: 深度学习画质：画质偏差。

#### test_samples\overexpose\over_2_g1.8.jpg (overexpose)
- 综合分: **51.3** (D 较差)
- 耗时: 225.2 ms
- 维度: {'deep_learning': 51.3}
- 评价: 深度学习画质：画质偏差。

#### test_samples\overexpose\over_3_g2.2.jpg (overexpose)
- 综合分: **47.6** (D 较差)
- 耗时: 242.7 ms
- 维度: {'deep_learning': 47.6}
- 评价: 深度学习画质：画质偏差。

#### test_samples\underexpose\under_1_g0.25.jpg (underexpose)
- 综合分: **4.9** (E 很差)
- 耗时: 229.8 ms
- 维度: {'deep_learning': 4.9}
- 评价: 深度学习画质：画质较差。

#### test_samples\underexpose\under_2_g0.4.jpg (underexpose)
- 综合分: **33.1** (E 很差)
- 耗时: 230.9 ms
- 维度: {'deep_learning': 33.1}
- 评价: 深度学习画质：画质较差。

#### test_samples\underexpose\under_3_g0.55.jpg (underexpose)
- 综合分: **43.2** (D 较差)
- 耗时: 236.7 ms
- 维度: {'deep_learning': 43.2}
- 评价: 深度学习画质：画质偏差。

#### test_samples\noise\noise_s15.jpg (noise)
- 综合分: **56.6** (D 较差)
- 耗时: 234.7 ms
- 维度: {'deep_learning': 56.6}
- 评价: 深度学习画质：画质一般。

#### test_samples\noise\noise_s30.jpg (noise)
- 综合分: **62.4** (C 一般)
- 耗时: 246.1 ms
- 维度: {'deep_learning': 62.4}
- 评价: 深度学习画质：画质一般。

#### test_samples\noise\noise_s50.jpg (noise)
- 综合分: **69.1** (C 一般)
- 耗时: 235.8 ms
- 维度: {'deep_learning': 69.1}
- 评价: 深度学习画质：画质一般。

#### test_samples\large\large_12mp.jpg (large)
- 综合分: **52.5** (D 较差)
- 耗时: 275.9 ms
- 维度: {'deep_learning': 52.5}
- 评价: 深度学习画质：画质偏差。

#### test_samples\counterexample\noise_masquerade_sharp.jpg (counterexample)
- 综合分: **61.4** (C 一般)
- 耗时: 236.8 ms
- 维度: {'deep_learning': 61.4}
- 评价: 深度学习画质：画质一般。

#### test_samples\counterexample\over_sharpened_halo.jpg (counterexample)
- 综合分: **68.1** (C 一般)
- 耗时: 236.2 ms
- 维度: {'deep_learning': 68.1}
- 评价: 深度学习画质：画质一般。

#### test_samples\counterexample\foggy_low_contrast.jpg (counterexample)
- 综合分: **52.0** (D 较差)
- 耗时: 219.2 ms
- 维度: {'deep_learning': 52.0}
- 评价: 深度学习画质：画质偏差。

#### test_samples\formats\sample.png (formats)
- 综合分: **51.8** (D 较差)
- 耗时: 240.6 ms
- 维度: {'deep_learning': 51.8}
- 评价: 深度学习画质：画质偏差。

#### test_samples\formats\sample.webp (formats)
- 综合分: **51.8** (D 较差)
- 耗时: 275.2 ms
- 维度: {'deep_learning': 51.8}
- 评价: 深度学习画质：画质偏差。

#### test_samples\formats\sample.jpg (formats)
- 综合分: **51.1** (D 较差)
- 耗时: 225.5 ms
- 维度: {'deep_learning': 51.1}
- 评价: 深度学习画质：画质偏差。

#### test_samples\formats\sample.heic (formats)
- 综合分: **52.5** (D 较差)
- 耗时: 296.5 ms
- 维度: {'deep_learning': 52.5}
- 评价: 深度学习画质：画质偏差。

### 模式：混合模式

#### test_samples\clear\clear_texture.jpg (clear)
- 综合分: **63.7** (C 一般)
- 耗时: 355.6 ms
- 维度: {'sharpness': 78.8, 'exposure': 96.0, 'noise': 68.7, 'contrast': 71.2, 'deep_learning': 48.4}
- 融合: 传统 78.98 + DL 48.4
- 评价: 清晰度：非常清晰 (已校正噪点)；曝光：曝光正常；噪点：噪点中等；对比度：对比度良好；深度学习画质：画质偏差。

#### test_samples\clear\clear_scene.jpg (clear)
- 综合分: **68.2** (C 一般)
- 耗时: 316.4 ms
- 维度: {'sharpness': 75.5, 'exposure': 95.9, 'noise': 95.3, 'contrast': 70.7, 'deep_learning': 51.5}
- 融合: 传统 84.83 + DL 51.5
- 评价: 清晰度：基本清晰；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质偏差。

#### test_samples\clear\clear_sharp.jpg (clear)
- 综合分: **70.9** (C 一般)
- 耗时: 300.8 ms
- 维度: {'sharpness': 78.7, 'exposure': 95.9, 'noise': 93.8, 'contrast': 70.8, 'deep_learning': 56.3}
- 融合: 传统 85.59 + DL 56.3
- 评价: 清晰度：基本清晰；曝光：曝光正常；噪点：噪点轻微；对比度：对比度良好；深度学习画质：画质一般。

#### test_samples\blur\blur_k5.jpg (blur)
- 综合分: **50.4** (D 较差)
- 耗时: 279.2 ms
- 维度: {'sharpness': 27.3, 'exposure': 95.9, 'noise': 98.0, 'contrast': 70.6, 'deep_learning': 36.6}
- 融合: 传统 64.17500000000001 + DL 36.6
- 评价: 清晰度：严重模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质较差。

#### test_samples\blur\blur_k15.jpg (blur)
- 综合分: **42.8** (D 较差)
- 耗时: 277.7 ms
- 维度: {'sharpness': 5.3, 'exposure': 95.9, 'noise': 98.8, 'contrast': 70.5, 'deep_learning': 36.6}
- 融合: 传统 48.959999999999994 + DL 36.6
- 评价: 清晰度：严重模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质较差。

#### test_samples\blur\blur_k31.jpg (blur)
- 综合分: **44.0** (D 较差)
- 耗时: 256.5 ms
- 维度: {'sharpness': 3.0, 'exposure': 95.8, 'noise': 99.4, 'contrast': 70.4, 'deep_learning': 40.6}
- 融合: 传统 47.46000000000001 + DL 40.6
- 评价: 清晰度：严重模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质偏差。

#### test_samples\overexpose\over_1_g1.4.jpg (overexpose)
- 综合分: **68.9** (C 一般)
- 耗时: 289.6 ms
- 维度: {'sharpness': 78.9, 'exposure': 82.7, 'noise': 95.8, 'contrast': 79.1, 'deep_learning': 53.6}
- 融合: 传统 84.105 + DL 53.6
- 评价: 清晰度：基本清晰；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质偏差。

#### test_samples\overexpose\over_2_g1.8.jpg (overexpose)
- 综合分: **65.0** (C 一般)
- 耗时: 297.0 ms
- 维度: {'sharpness': 77.8, 'exposure': 67.2, 'noise': 96.5, 'contrast': 75.3, 'deep_learning': 51.3}
- 融合: 传统 78.61 + DL 51.3
- 评价: 清晰度：基本清晰；曝光：整体偏亮；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质偏差。

#### test_samples\overexpose\over_3_g2.2.jpg (overexpose)
- 综合分: **56.0** (D 较差)
- 耗时: 278.3 ms
- 维度: {'sharpness': 78.6, 'exposure': 43.7, 'noise': 97.4, 'contrast': 63.1, 'deep_learning': 47.6}
- 融合: 传统 64.36 + DL 47.6
- 评价: 清晰度：基本清晰；曝光：过曝；噪点：噪点极低；对比度：对比度一般；深度学习画质：画质偏差。

#### test_samples\underexpose\under_1_g0.25.jpg (underexpose)
- 综合分: **15.9** (E 很差)
- 耗时: 276.4 ms
- 维度: {'sharpness': 13.0, 'exposure': 53.8, 'noise': 95.2, 'contrast': 20.6, 'deep_learning': 4.9}
- 融合: 传统 26.92 + DL 4.9
- 评价: 清晰度：严重模糊；曝光：整体偏暗；噪点：噪点极低；对比度：对比度偏低；深度学习画质：画质较差。

#### test_samples\underexpose\under_2_g0.4.jpg (underexpose)
- 综合分: **40.7** (D 较差)
- 耗时: 291.9 ms
- 维度: {'sharpness': 31.5, 'exposure': 62.2, 'noise': 95.7, 'contrast': 32.9, 'deep_learning': 33.1}
- 融合: 传统 48.30500000000001 + DL 33.1
- 评价: 清晰度：明显模糊；曝光：整体偏暗；噪点：噪点极低；对比度：对比度偏低；深度学习画质：画质较差。

#### test_samples\underexpose\under_3_g0.55.jpg (underexpose)
- 综合分: **53.7** (D 较差)
- 耗时: 289.8 ms
- 维度: {'sharpness': 46.4, 'exposure': 70.5, 'noise': 95.8, 'contrast': 44.0, 'deep_learning': 43.2}
- 融合: 传统 64.26499999999999 + DL 43.2
- 评价: 清晰度：明显模糊；曝光：整体偏暗；噪点：噪点极低；对比度：对比度一般；深度学习画质：画质偏差。

#### test_samples\noise\noise_s15.jpg (noise)
- 综合分: **70.7** (C 一般)
- 耗时: 285.1 ms
- 维度: {'sharpness': 89.7, 'exposure': 95.6, 'noise': 75.1, 'contrast': 71.2, 'deep_learning': 56.6}
- 融合: 传统 84.75 + DL 56.6
- 评价: 清晰度：非常清晰；曝光：曝光正常；噪点：噪点中等；对比度：对比度良好；深度学习画质：画质一般。

#### test_samples\noise\noise_s30.jpg (noise)
- 综合分: **63.4** (C 一般)
- 耗时: 277.4 ms
- 维度: {'sharpness': 56.4, 'exposure': 95.6, 'noise': 57.3, 'contrast': 72.5, 'deep_learning': 62.4}
- 融合: 传统 64.39500000000001 + DL 62.4
- 评价: 清晰度：假性清晰(严重噪点)；曝光：曝光正常；噪点：噪点明显；对比度：对比度良好；深度学习画质：画质一般。

#### test_samples\noise\noise_s50.jpg (noise)
- 综合分: **53.6** (D 较差)
- 耗时: 291.6 ms
- 维度: {'sharpness': 26.7, 'exposure': 95.7, 'noise': 38.2, 'contrast': 74.4, 'deep_learning': 69.1}
- 融合: 传统 38.19500000000001 + DL 69.1
- 评价: 清晰度：假性清晰(严重噪点)；曝光：曝光正常；噪点：噪点明显；对比度：对比度良好；深度学习画质：画质一般。

#### test_samples\large\large_12mp.jpg (large)
- 综合分: **67.1** (C 一般)
- 耗时: 345.5 ms
- 维度: {'sharpness': 65.1, 'exposure': 95.6, 'noise': 97.6, 'contrast': 70.8, 'deep_learning': 52.5}
- 融合: 传统 81.705 + DL 52.5
- 评价: 清晰度：轻度模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质偏差。

#### test_samples\counterexample\noise_masquerade_sharp.jpg (counterexample)
- 综合分: **54.9** (D 较差)
- 耗时: 288.5 ms
- 维度: {'sharpness': 33.2, 'exposure': 96.2, 'noise': 47.4, 'contrast': 74.0, 'deep_learning': 61.4}
- 融合: 传统 48.330000000000005 + DL 61.4
- 评价: 清晰度：假性清晰(严重噪点)；曝光：曝光正常；噪点：噪点明显；对比度：对比度良好；深度学习画质：画质一般。

#### test_samples\counterexample\over_sharpened_halo.jpg (counterexample)
- 综合分: **78.4** (B 良好)
- 耗时: 299.8 ms
- 维度: {'sharpness': 94.5, 'exposure': 95.9, 'noise': 84.0, 'contrast': 71.3, 'deep_learning': 68.1}
- 融合: 传统 88.74499999999999 + DL 68.1
- 评价: 清晰度：清晰；曝光：曝光正常；噪点：噪点轻微；对比度：对比度良好；深度学习画质：画质一般。

#### test_samples\counterexample\foggy_low_contrast.jpg (counterexample)
- 综合分: **48.8** (D 较差)
- 耗时: 282.5 ms
- 维度: {'sharpness': 25.4, 'exposure': 65.7, 'noise': 99.1, 'contrast': 28.8, 'deep_learning': 52.0}
- 融合: 传统 45.58 + DL 52.0
- 评价: 清晰度：严重模糊；曝光：整体偏亮；噪点：噪点极低；对比度：对比度偏低；深度学习画质：画质偏差。

#### test_samples\formats\sample.png (formats)
- 综合分: **68.1** (C 一般)
- 耗时: 311.6 ms
- 维度: {'sharpness': 74.2, 'exposure': 95.9, 'noise': 95.6, 'contrast': 70.7, 'deep_learning': 51.8}
- 融合: 传统 84.45 + DL 51.8
- 评价: 清晰度：轻度模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质偏差。

#### test_samples\formats\sample.webp (formats)
- 综合分: **68.1** (C 一般)
- 耗时: 325.0 ms
- 维度: {'sharpness': 74.2, 'exposure': 95.9, 'noise': 95.6, 'contrast': 70.7, 'deep_learning': 51.8}
- 融合: 传统 84.45 + DL 51.8
- 评价: 清晰度：轻度模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质偏差。

#### test_samples\formats\sample.jpg (formats)
- 综合分: **67.7** (C 一般)
- 耗时: 285.2 ms
- 维度: {'sharpness': 73.5, 'exposure': 95.9, 'noise': 95.8, 'contrast': 70.7, 'deep_learning': 51.1}
- 融合: 传统 84.255 + DL 51.1
- 评价: 清晰度：轻度模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质偏差。

#### test_samples\formats\sample.heic (formats)
- 综合分: **68.0** (C 一般)
- 耗时: 333.3 ms
- 维度: {'sharpness': 71.0, 'exposure': 95.9, 'noise': 96.1, 'contrast': 70.7, 'deep_learning': 52.5}
- 融合: 传统 83.455 + DL 52.5
- 评价: 清晰度：轻度模糊；曝光：曝光正常；噪点：噪点极低；对比度：对比度良好；深度学习画质：画质偏差。

## 反例深度分析（传统算法）

> 以下反例展示了传统 CV 画质评分算法的**固有局限性**。每个反例都代表一种常见的评分失准模式。

### 反例：`test_samples\counterexample\noise_masquerade_sharp.jpg`

| 指标 | 值 |
|------|-----|
| 综合分 | **48.3** (D 较差) |
| 清晰度（原始 Laplacian） | 100.0 |
| 清晰度（校正后） | 33.2 |
| 噪点分 | 47.4 |
| 曝光分 | 96.2 |
| 对比度分 | 74.0 |

**人工判断**：画质差——强颗粒噪点充斥画面，细节完全被噪点掩盖，主观画质差

**预期失准点**：Laplacian 方差因噪点高频能量而虚高，清晰度分可能 ≥ 80

**根因分析**：Laplacian 算子检测的是二阶导数能量，无法区分「纹理边缘」和「随机噪点」。颗粒噪点（高 ISO 模拟）产生大量高频响应，方差被显著抬高。虽有噪点交叉校正（scorer.py），但当 noise_level 与 variance 均极高时，校正力度不足以完全消除虚高。

**深度学习模式对比**：综合分 **61.4** — 深度学习画质：画质一般。

---

### 反例：`test_samples\counterexample\over_sharpened_halo.jpg`

| 指标 | 值 |
|------|-----|
| 综合分 | **88.7** (B 良好) |
| 清晰度（原始 Laplacian） | 94.5 |
| 清晰度（校正后） | 94.5 |
| 噪点分 | 84.0 |
| 曝光分 | 95.9 |
| 对比度分 | 71.3 |

**人工判断**：画质差——过度 USM 锐化产生明显光晕和边缘伪影，视觉不自然

**预期失准点**：Laplacian 方差因锐化后的强边缘而极高，清晰度分接近满分

**根因分析**：Unsharp Mask 锐化通过增强边缘对比度来提升「清晰感」，Laplacian 方差直接反映这种增强，因此打出高分。但过度锐化会产生 halo（光晕）和振铃效应，人眼感知为伪影而非真正清晰。当前算法缺乏对锐化伪影的检测（如 overshoot 检测）。

**深度学习模式对比**：综合分 **68.1** — 深度学习画质：画质一般。

---

### 反例：`test_samples\counterexample\foggy_low_contrast.jpg`

| 指标 | 值 |
|------|-----|
| 综合分 | **45.6** (D 较差) |
| 清晰度（原始 Laplacian） | 25.4 |
| 清晰度（校正后） | 25.4 |
| 噪点分 | 99.1 |
| 曝光分 | 65.7 |
| 对比度分 | 28.8 |

**人工判断**：画质差——雾天场景，画面发灰、对比度极低，细节不可辨

**预期失准点**：曝光维度可能正常（均值接近 128），但对比度和清晰度应偏低

**根因分析**：曝光算法基于全局亮度均值和裁剪率，雾天场景亮度均值可能接近理想区间，因此曝光分不会很低。但人眼感知的是信息量（对比度、细节），而非仅仅是亮度。对比度维度（RMS）能捕捉到此问题，但权重仅 15%，可能不足以将综合分拉低到与主观感受一致的水平。

**深度学习模式对比**：综合分 **52.0** — 深度学习画质：画质偏差。

---

## 评分结果 vs 人工判断对比

| 类别 | 样本 | 综合分 | 清晰度 | 曝光 | 噪点 | 对比度 | 人工判断 | 一致？ |
|------|------|--------|--------|------|------|--------|----------|--------|
| clear | clear_texture.jpg | 79.0 | 78.8 | 96.0 | 68.7 | 71.2 | 高 | ✅ |
| clear | clear_scene.jpg | 84.8 | 75.5 | 95.9 | 95.3 | 70.7 | 高 | ✅ |
| clear | clear_sharp.jpg | 85.6 | 78.7 | 95.9 | 93.8 | 70.8 | 高 | ✅ |
| blur | blur_k5.jpg | 64.2 | 27.3 | 95.9 | 98.0 | 70.6 | 低 | ✅ |
| blur | blur_k15.jpg | 49.0 | 5.3 | 95.9 | 98.8 | 70.5 | 低 | ✅ |
| blur | blur_k31.jpg | 47.5 | 3.0 | 95.8 | 99.4 | 70.4 | 低 | ✅ |
| overexpose | over_1_g1.4.jpg | 84.1 | 78.9 | 82.7 | 95.8 | 79.1 | 低 | ⚠️ |
| overexpose | over_2_g1.8.jpg | 78.6 | 77.8 | 67.2 | 96.5 | 75.3 | 低 | ✅ |
| overexpose | over_3_g2.2.jpg | 64.4 | 78.6 | 43.7 | 97.4 | 63.1 | 低 | ✅ |
| underexpose | under_1_g0.25.jpg | 26.9 | 13.0 | 53.8 | 95.2 | 20.6 | 低 | ✅ |
| underexpose | under_2_g0.4.jpg | 48.3 | 31.5 | 62.2 | 95.7 | 32.9 | 低 | ✅ |
| underexpose | under_3_g0.55.jpg | 64.3 | 46.4 | 70.5 | 95.8 | 44.0 | 低 | ⚠️ |
| noise | noise_s15.jpg | 84.8 | 89.7 | 95.6 | 75.1 | 71.2 | 低 | ✅ |
| noise | noise_s30.jpg | 64.4 | 56.4 | 95.6 | 57.3 | 72.5 | 低 | ✅ |
| noise | noise_s50.jpg | 38.2 | 26.7 | 95.7 | 38.2 | 74.4 | 低 | ✅ |
| large | large_12mp.jpg | 81.7 | 65.1 | 95.6 | 97.6 | 70.8 | 中 | — |
| counterexample | noise_masquerade_sharp.jpg | 48.3 | 33.2 | 96.2 | 47.4 | 74.0 | 失准 | ❌ 失准 |
| counterexample | over_sharpened_halo.jpg | 88.7 | 94.5 | 95.9 | 84.0 | 71.3 | 失准 | ❌ 失准 |
| counterexample | foggy_low_contrast.jpg | 45.6 | 25.4 | 65.7 | 99.1 | 28.8 | 失准 | ❌ 失准 |
| formats | sample.png | 84.5 | 74.2 | 95.9 | 95.6 | 70.7 | 一致 | — |
| formats | sample.webp | 84.5 | 74.2 | 95.9 | 95.6 | 70.7 | 一致 | — |
| formats | sample.jpg | 84.3 | 73.5 | 95.9 | 95.8 | 70.7 | 一致 | — |
| formats | sample.heic | 83.5 | 71.0 | 95.9 | 96.1 | 70.7 | 一致 | — |
