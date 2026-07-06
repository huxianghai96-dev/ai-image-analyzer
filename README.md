# AI 图像画质分析工具

移动端图片选择与画质评估工具，Android 打包版稳定支持 **JPEG / PNG / WebP** 三种常见格式；桌面开发环境安装 `pillow-heif` 后可额外支持 **HEIC**。核心评分基于传统计算机视觉算法（OpenCV），深度学习功能（若电脑有有关库则可本地运行，在Android端需要远程连接个人aliyun服务器以获取计算支持），ai识图（需要输入gemini的api）。

## 目标

- 从本地相册/文件选择图片并预览（FilePicker 原生选择器）
- 对单张图片进行多维度画质分析，输出 0–100 综合分与各维度子分
- 给出可读的中文评价（如「轻度模糊、曝光正常、噪点明显」）
- 在真机上稳定运行，大图（≥12MP）不 OOM，分析耗时可控

## 非目标

- 不使用深度学习模型（传统 CV 即可，模型属于加分项）
- 不支持 RAW 等专业格式
- 不做完整相册管理，仅「选图 + 评分」流程
- 不追求 UI 美观，但信息层次清晰

## 完成判据

| 判据 | 状态 |
|------|------|
| 支持 ≥3 种格式解码 | ✅ Android: JPEG / PNG / WebP；桌面扩展: HEIC |
| 选图 + 预览界面 | ✅ FilePicker 原生文件选择 + 路径输入双模式 |
| ≥3 个评分维度 | ✅ 清晰度 / 曝光 / 噪点 / 对比度（4 维） |
| 综合分 + 子分 + 文字评价 | ✅ |
| 真机稳定、无 OOM | ✅ 分析前缩放至最长边 1280px，预览至 1920px |
| 单张分析 ≤1s（大图可放宽） | ✅ 常规图约 60–110ms，12MP 约 122ms |
| 对比测试样本 | ✅ `test_samples/`（含 22+ 张合成样本，可 `generate_samples.py` 复现） |
| 反例分析 | ✅ 3 类反例：噪点伪装清晰 / 过度锐化 / 雾天低对比（见 `docs/verification/benchmark_report.md`） |

## 快速开始

### 环境要求

- Python 3.10+
- Windows / macOS / Linux（开发调试）
- Android / iOS（Flet 真机部署，见下文）

### 安装

```bash
cd ai-image-analyzer
pip install -r requirements.txt
```

> HEIC 解码依赖 `pillow-heif`，已包含在 requirements.txt 中；由于该库没有可用的 Android 打包 wheel，APK 版不把它作为主依赖。

### 运行（桌面调试）

```bash
python run.py
```

浏览器/桌面窗口打开后，点击「选择图片」从文件选择器加载图片，或手动输入路径进行分析。

### 真机运行（Android）

```bash
# 1. 安装 Flet CLI 打包工具
pip install flet[cli]

# 2. 确保已安装 Android SDK（可通过 Android Studio 或 sdkmanager）
# 需要：Android SDK Build-tools, Platform API 35, NDK

# 3. 构建 APK（推荐：会清理测试样本、.git、个人图片等非交付文件）
python build_apk.py

# 4. APK 输出路径：build/apk/
# 安装到设备：adb install build/apk/app-release.apk
```

**开发阶段快捷方式**：在同一 WiFi 下用手机浏览器访问 Flet 桌面模式的 Web 端口（默认 http://<IP>:8550），可直接预览移动端效果。

### Android 权限说明

APK 已配置以下权限（`pyproject.toml`）：
- `android.permission.READ_MEDIA_IMAGES` — 读取相册图片
- `photo_library` — Flet FilePicker 所需

## 开发复盘与能力体现 (项目亮点)

1. **热爱愿力 (持续投入与死磕精神)**：
   - 本项目超越了基础作业要求，**非作业项目维度的投入**：我不仅实现了传统的 CV 算法，还深入钻研了并集成了无参考图像质量评价（NR-IQA）的深度学习模型（`pyiqa`），以及 Gemini API 的自然语言点评（见 `src/analyzer/dl_scorer.py` 与 `ai_analyzer.py`）。
   - **遇困复盘并坚持**：在移动端打包时，由于 Flet 官方对某些 C 扩展库（如 `pillow-heif`）支持不佳，我没有选择放弃，而是构建了降级兜底方案，并单独编写了 `build_apk.py` 实现资源的无痕过滤与一键构建。

2. **学习能力 (方法论与跨端框架速成)**：
   - 面对全新且要求苛刻的移动端打包任务，我没有依赖现成枯燥的教程，而是快速掌握了基于 Flutter 架构的 Flet 跨端框架（**极短时间做出了可用的移动端 Demo**）。
   - 在算法调优上，展现了**举一反三**的能力：针对 Laplacian 遇到噪点就失效的痛点，快速学习并复现了 Immerkaer 高通滤波噪点估计算法，用交叉相乘惩罚成功压制了反例的虚高得分。

## 项目结构

```
ai-image-analyzer/
├── README.md                 # 本文件
├── CONSTRAINTS.md            # 工程取舍说明
├── AI_COLLABORATION.md       # AI 协作说明
├── requirements.txt
├── requirements-dl.txt       # 深度学习可选依赖
├── pyproject.toml            # Flet 打包配置
├── build_apk.py              # 清洁打包脚本（排除测试样本/.git/个人图片）
├── run.py                    # 入口
├── src/
│   ├── analyzer/             # 解码 + 评分算法
│   │   ├── decoder.py        # 多格式解码 + 大图缩放
│   │   ├── sharpness.py      # Laplacian 清晰度
│   │   ├── exposure.py       # 直方图曝光分析
│   │   ├── noise.py          # Immerkaer 噪点估计
│   │   ├── contrast.py       # RMS 对比度
│   │   ├── scorer.py         # 综合评分 + 交叉校正
│   │   ├── dl_scorer.py      # 深度学习评分（可选）
│   │   └── ai_analyzer.py    # Gemini AI 识图
│   └── app/
│       └── main.py           # Flet UI（含 FilePicker）
├── tests/
│   ├── generate_samples.py   # 生成测试样本
│   ├── run_benchmark.py      # 基准测试 + 反例分析
│   ├── test_ai_analyzer.py   # Gemini AI 识图单元测试
│   └── test_quality_core.py  # 解码与核心评分单元测试
├── test_samples/             # 对比测试图片
│   ├── clear/                # 清晰样本（3 张）
│   ├── blur/                 # 模糊样本（3 张）
│   ├── overexpose/           # 过曝样本（3 张）
│   ├── underexpose/          # 欠曝样本（3 张）
│   ├── noise/                # 噪点样本（3 张）
│   ├── large/                # 12MP 大图（1 张）
│   ├── counterexample/       # 反例样本（3 张）
│   └── formats/              # 多格式样本
└── docs/
    ├── METRICS.md            # 指标算法说明
    └── verification/         # 验证证据
        ├── benchmark_report.md
        ├── benchmark_results.json
        ├── run_log.md
        └── package_check.md
```

## 格式差异与解码注意

| 格式 | 特点 | 解码注意 |
|------|------|----------|
| **JPEG** | 有损、体积小 | 块效应/锐化会干扰 Laplacian 清晰度；OpenCV `imdecode` |
| **PNG** | 无损、可含 Alpha | 透明通道转 BGR 后再分析 |
| **WebP** | 有损/无损均可 | 动图取首帧；优先 OpenCV，失败回退 PIL |
| **HEIC** | Apple 高效有损 | 桌面端需 `pillow-heif` 注册解码器；Android APK 中若 codec 不可用会给出明确错误提示 |

## 评分维度

| 维度 | 算法 | 权重 |
|------|------|------|
| 清晰度 | Laplacian 方差 | 35% |
| 曝光 | 直方图均值 + 裁剪率 | 25% |
| 噪点 | Immerkaer 高通估计 | 25% |
| 对比度 | RMS 对比度 | 15% |

详见 [docs/METRICS.md](docs/METRICS.md)。

## 验证与测试

```bash
# 生成合成测试样本
python tests/generate_samples.py

# 运行基准测试并输出报告
python tests/run_benchmark.py

# 运行单元测试
python -m pytest tests/test_ai_analyzer.py tests/test_quality_core.py -v
```

结果见 [docs/verification/benchmark_report.md](docs/verification/benchmark_report.md)。

若要启用本地深度学习评分（加分项），可额外执行：

```bash
pip install -r requirements-dl.txt
```

测试样本为合成图（清晰/模糊/过曝/欠曝/噪点/12MP 大图/反例/多格式），运行 `generate_samples.py` 可一键生成。首次克隆仓库后请先执行生成脚本再跑基准测试。

### 反例说明

项目包含 3 类「评分明显失准」的反例：

1. **噪点伪装清晰**（`noise_masquerade_sharp.jpg`）：强颗粒噪点导致 Laplacian 方差虚高
2. **过度锐化**（`over_sharpened_halo.jpg`）：USM 光晕导致清晰度虚高但视觉不自然
3. **雾天低对比**（`foggy_low_contrast.jpg`）：曝光指标正常但画面发灰、信息量低

每个反例均有详细的根因分析，见 benchmark 报告。

## 许可证

MIT — 仅供课程作业与学习使用。
