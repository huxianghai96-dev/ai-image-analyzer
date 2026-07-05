# 评分指标说明

本文档说明各画质维度的算法来源、参数含义与局限性。

---

## 1. 清晰度（Sharpness）

### 算法

**Laplacian 方差法**（Variance of Laplacian）

```python
gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
lap = cv2.Laplacian(gray, cv2.CV_64F, ksize=3)
variance = lap.var()
```

### 来源

- Pech-Pacheco et al., *"Diagnosis of blur in digital images"*, SPIE 2000
- 广泛使用于无参考模糊检测

### 参数含义

| 参数 | 值 | 含义 |
|------|-----|------|
| `ksize` | 3 | Laplacian 核大小 |
| `variance` | 原始值 | 图像二阶导数能量；越大通常越清晰 |
| 映射阈值 | 20/80/200/500/1200 | 经验值，将 variance 映射到 0–100 |

### 局限性

- **对噪点敏感**：随机颗粒会抬高方差，可能误判为「非常清晰」（见反例 `noise_masquerade_sharp.jpg`）
- **对锐化/压缩伪影敏感**：Unsharp Mask、JPEG 块边界会产生高频能量
- **无方向性**：无法区分运动模糊方向
- **依赖场景纹理**：无纹理区域（天空、墙面）方差天然偏低

### 噪点交叉校正（综合层）

当 `noise_level > 6` 且 `laplacian_variance > 120` 时，在 `scorer.py` 中下调清晰度分：

```
excess = min(1, (noise_level - 6) / 18)
adjusted = sharp_score × (1 - 0.75×excess) + noise_score × 0.2×excess
```

用于缓解噪点伪装清晰的问题，但无法完全消除（见反例分析）。

---

## 2. 曝光（Exposure）

### 算法

**全局亮度直方图分析**

- 计算灰度均值 `mean_brightness`
- 统计暗部裁剪率 `dark_clip_ratio`（像素值 0–7 占比）
- 统计亮部裁剪率 `bright_clip_ratio`（像素值 248–255 占比）
- 综合打分：`mean_score × 0.6 + (100 - clip_penalty) × 0.4`

### 来源

基于经典直方图分析，参考相机曝光评价常用启发式。

### 参数含义

| 参数 | 含义 |
|------|------|
| `mean_brightness` | 理想约 128；偏离越大扣分 |
| `dark_clip_ratio > 0.05` | 判定「欠曝」 |
| `bright_clip_ratio > 0.05` | 判定「过曝」 |

### 局限性

- **仅全局**：无法检测局部过曝/欠曝（如逆光人像）
- **不区分意图**：高键/低键摄影可能被误判
- **忽略色彩**：仅使用亮度通道

---

## 3. 噪点（Noise）

### 算法

**Immerkaer 高通滤波估计**（1996）

```python
kernel = [[1,-2,1], [-2,4,-2], [1,-2,1]]
response = cv2.filter2D(gray, -1, kernel)
sigma = mean(abs(response)) * sqrt(pi/2) / 6
```

### 来源

- Immerkaer, J., *"Fast Noise Variance Estimation"*, CVPR 1996
- 利用邻域像素与拉普lasian 类似核的快速噪声标准差估计

### 参数含义

| sigma 范围 | 映射分数 | 标签 |
|------------|----------|------|
| < 2.5 | 95–100 | 噪点极低 |
| 2.5–6 | 75–95 | 轻微 |
| 6–12 | 50–75 | 中等 |
| 12–22 | 25–50 | 明显 |
| > 22 | 0–25 | 严重 |

### 局限性

- **纹理干扰**：强周期性纹理（织物、砖墙）可能抬高 sigma
- **仅估计强度**：不区分高斯噪点、椒盐、压缩伪影
- **JPEG 块效应**：可能被部分计入噪点

---

## 4. 对比度（Contrast）

### 算法

**RMS 对比度**（Root Mean Square Contrast）

```python
rms = sqrt(mean((gray - mean(gray))^2))
```

### 来源

标准图像质量教材中的全局对比度度量（Peli, 1990 等）。

### 参数含义

| RMS 范围 | 标签 |
|----------|------|
| < 15 | 对比度偏低 |
| 15–30 | 一般 |
| 30–55 | 良好 |
| > 55 | 优秀 |

### 局限性

- **全局统计**：忽略局部对比度（微对比）
- **与曝光耦合**：过暗/过亮图像 RMS 可能异常

---

## 5. 综合分

```
overall = sharpness×0.35 + exposure×0.25 + noise×0.25 + contrast×0.15
```

权重依据：清晰度与噪点对人眼画质感知影响最大，曝光次之，对比度辅助。

### 缺陷惩罚

为避免单项严重缺陷被其他高分维度掩盖，综合分会在加权后应用轻量惩罚：

- 清晰度 < 40：按 `(40 - sharpness) × 0.35` 扣分
- 曝光 < 70：按 `(70 - exposure) × 0.30` 扣分
- 噪点 < 70：按 `(70 - noise) × 0.35` 扣分
- 对比度 < 45：按 `(45 - contrast) × 0.15` 扣分

总惩罚最多 25 分。该步骤只校准最终综合分，不改变各维度子分和标签，因此仍能追溯每个指标的原始判断。

### 等级

| 分数 | 等级 |
|------|------|
| ≥ 90 | A 优秀 |
| ≥ 75 | B 良好 |
| ≥ 60 | C 一般 |
| ≥ 40 | D 较差 |
| < 40 | E 很差 |

---

## 6. 性能与预处理

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `ANALYSIS_MAX_EDGE` | 1280 | 分析前最长边缩放，防 OOM |
| `PREVIEW_MAX_EDGE` | 1920 | 预览图缩放 |

### 耗时参考（本机实测）

| 场景 | 耗时 |
|------|------|
| 1600×1200 JPEG | ~60–110 ms |
| 4000×3000 (12MP) JPEG | ~122 ms |
| 首次解码（含 IO） | 可能 +200 ms |

大图适当放宽至 1s 以内；若保留原分辨率，12MP Laplacian 约需 300–800ms 且内存占用 ~140MB。
