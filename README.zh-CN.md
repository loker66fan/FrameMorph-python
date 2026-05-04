# FrameMorph-python

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](requirements.txt)
[![UI](https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt&logoColor=white)](README.md)
[![License](https://img.shields.io/badge/License-MIT-black)](LICENSE)
[![Windows Portable Build](https://github.com/loker66fan/FrameMorph-python/actions/workflows/windows-portable-build.yml/badge.svg)](https://github.com/loker66fan/FrameMorph-python/actions/workflows/windows-portable-build.yml)

基于 `PySide6`、`Pillow`、`OpenCV` 和 `NumPy` 构建的桌面图像编辑工具，面向本地、实用、可控的图像处理工作流。

[English README](README.md)

`FrameMorph-python` 是仓库名，“形绘”是面向最终用户展示的桌面应用名称。

## 项目概览

这个项目聚焦本地图像编辑的常用操作，而不是依赖在线服务或模板化流程。

- 自由裁剪和比例裁剪
- 缩放、拉伸、旋转
- 网格变形与透视矫正
- 画布文字叠加
- 高清导出
- 多种增强路径，包括 OpenCV `dnn_superres`

## 截图

| 工作台 | 网格变形 | 导出面板 |
| --- | --- | --- |
| ![Workbench](assets/screenshots/workbench.png) | ![Mesh Warp](assets/screenshots/mesh-warp.png) | ![Export Panel](assets/screenshots/export-panel.png) |

## 快速开始

### 环境要求

- Python 3.11+

### 安装

```bash
pip install -r requirements.txt
```

### 运行

```bash
python main.py
```

## 主要特性

- 支持拖拽导入图片
- 画布常驻，右侧面板切换控制功能
- 支持撤销与重做
- 网格变形与透视变换支持实时预览
- 导出前后增强预览
- 导出支持后台进度、预计剩余时间和取消
- 支持 OpenCV 超分模型下载与本地模型使用

## 增强与导出

当前导出增强支持三种路径：

1. 内置经典超分增强
2. 使用自定义本地模型路径的 PyTorch SRCNN
3. OpenCV `dnn_superres`

支持的 OpenCV 模型系列：

- EDSR
- ESPCN
- FSRCNN
- LapSRN

应用支持：

- 从 `.pb` 文件名自动识别模型类型和倍率
- 将支持的 OpenCV 模型下载到 `models/opencv_dnn_superres/`
- 导出时显示百分比和预计剩余时间

## 仓库结构

```text
FrameMorph-python/
├── main.py
├── core/
├── ui/
├── utils/
├── docs/
├── assets/
│   └── screenshots/
├── models/
│   └── opencv_dnn_superres/
├── release/
│   └── windows-portable/
├── VERSION
├── CHANGELOG.md
├── PROJECT_SUMMARY.md
└── requirements.txt
```

## 文档

- 技术维护文档：[docs/TECHNICAL.md](docs/TECHNICAL.md)
- 使用文档：[docs/USER_GUIDE.md](docs/USER_GUIDE.md)
- 发布元信息文档：[docs/RELEASE.md](docs/RELEASE.md)
- 中文发布说明：[docs/RELEASE.zh-CN.md](docs/RELEASE.zh-CN.md)
- 打包说明：[docs/PACKAGING.md](docs/PACKAGING.md)
- GitHub Actions Windows 自动构建：[docs/GITHUB_ACTIONS_WINDOWS_BUILD.md](docs/GITHUB_ACTIONS_WINDOWS_BUILD.md)
- 项目简介：[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- 变更记录：[CHANGELOG.md](CHANGELOG.md)
- Windows 便携版构建目录：[release/windows-portable](release/windows-portable)

## 版本

当前版本：`0.1.0`

详见 [VERSION](VERSION)。

## 许可证

MIT License，详见 [LICENSE](LICENSE)。
