# AI 图像画质分析工具

移动端图片选择与画质评估工具，支持 **JPEG / PNG / WebP / HEIC** 四种常见格式，基于传统计算机视觉算法（OpenCV），无需深度学习模型与联网。

## 目标

- 从本地相册/文件选择图片并预览
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
| 支持 ≥3 种格式解码 | ✅ JPEG / PNG / WebP / HEIC |
| 选图 + 预览界面 | ✅ Flet 移动端 UI |
| ≥3 个评分维度 | ✅ 清晰度 / 曝光 / 噪点 / 对比度（4 维） |
| 综合分 + 子分 + 文字评价 | ✅ |
| 真机稳定、无 OOM | ✅ 分析前缩放至最长边 1280px，预览至 1920px |
| 单张分析 ≤1s（大图可放宽） | ✅ 常规图 ~40–70ms，12MP ~92ms |
| 对比测试样本 | ✅ `test_samples/`（含 18 张合成样本，可 `generate_samples.py` 复现） |
| 反例分析 | ✅ 见 `docs/verification/benchmark_report.md` |

## 快速开始

### 环境要求

- Python 3.10+
- Windows / macOS / Linux（开发调试）
- Android / iOS（Flet 真机部署，见下文）

### 安装

```bash
cd image-quality-analyzer
pip install -r requirements.txt
```

> HEIC 解码依赖 `pillow-heif`，已包含在 requirements.txt 中。

### 运行（桌面调试）

```bash
python run.py
```

浏览器/桌面窗口打开后，点击「选择图片」加载本地文件即可分析。

### 真机运行（Android）

```bash
# 首次需安装 Flet CLI 打包工具
pip install flet[cli]

# 构建 APK（需 Android SDK / 连接设备）
flet build apk -v
```

也可在同一 WiFi 下用手机浏览器访问 Flet 桌面模式的 Web 端口进行演示（开发阶段）。

## 项目结构

```
image-quality-analyzer/
├── README.md                 # 本文件
├── CONSTRAINTS.md            # 工程取舍说明
├── AI_COLLABORATION.md       # AI 协作说明
├── requirements.txt
├── run.py                    # 入口
├── src/
│   ├── analyzer/             # 解码 + 评分算法
│   └── app/                  # Flet UI
├── tests/
│   ├── generate_samples.py   # 生成测试样本
│   └── run_benchmark.py      # 基准测试
├── test_samples/             # 对比测试图片
└── docs/
    ├── METRICS.md            # 指标算法说明
    └── verification/         # 验证证据
```

## 格式差异与解码注意

| 格式 | 特点 | 解码注意 |
|------|------|----------|
| **JPEG** | 有损、体积小 | 块效应/锐化会干扰 Laplacian 清晰度；OpenCV `imdecode` |
| **PNG** | 无损、可含 Alpha | 透明通道转 BGR 后再分析 |
| **WebP** | 有损/无损均可 | 动图取首帧；优先 OpenCV，失败回退 PIL |
| **HEIC** | Apple 高效有损 | 需 `pillow-heif` 注册解码器，成本高于 JPEG |

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
```

结果见 [docs/verification/benchmark_report.md](docs/verification/benchmark_report.md)。

测试样本为合成图（清晰/模糊/过曝/欠曝/噪点/12MP 大图/反例/多格式），运行 `generate_samples.py` 可一键生成。首次克隆仓库后请先执行生成脚本再跑基准测试。

## 许可证

MIT — 仅供课程作业与学习使用。
