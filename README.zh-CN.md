# FrameMorph-python

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](requirements.txt)
[![UI](https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt&logoColor=white)](README.md)
[![License](https://img.shields.io/badge/License-MIT-black)](LICENSE)
[![Windows Portable Build](https://github.com/loker66fan/FrameMorph-python/actions/workflows/windows-portable-build.yml/badge.svg)](https://github.com/loker66fan/FrameMorph-python/actions/workflows/windows-portable-build.yml)

基于 `PySide6`、`Pillow`、`OpenCV` 和 Python 文档处理库构建的本地桌面工具，覆盖图片编辑、文档转换、PDF 处理、OCR 工作流和高清导出。

[English README](README.md)

`FrameMorph-python` 是仓库名，“形绘”是面向最终用户展示的桌面应用名称。

## 项目概览

这个项目聚焦本地文件处理和图片编辑，而不是依赖在线服务或模板化流程。

- 文档工作台：覆盖 Office、PDF、图片、OCR 和去水印相关任务
- 图片工作台：支持裁剪、缩放、拉伸、旋转、网格变形、透视矫正和文字叠加
- 任务队列：支持状态跟踪、日志、批量执行和可配置输出目录
- 高清图片导出：支持多种增强路径，包括 OpenCV `dnn_superres`
- 设置页：管理主题、字体大小、默认输出目录和本地后端状态

## 截图

| 文档工作台 | 图片工作台 | 导出面板 |
| --- | --- | --- |
| ![Document Workbench](assets/screenshots/document-workbench.png) | ![Image Workbench](assets/screenshots/workbench.png) | ![Export Panel](assets/screenshots/export-panel.png) |

| 网格变形 | 设置页 |
| --- | --- |
| ![Mesh Warp](assets/screenshots/mesh-warp.png) | ![Settings](assets/screenshots/settings-page.png) |

## 快速开始

### 环境要求

- Python 3.11+

### 安装

```bash
pip install -r requirements.txt
```

如果要执行 Windows 便携版打包，请改用专用构建依赖清单：

```bash
pip install -r release/windows-portable/requirements-windows-build.txt
```

日常开发和应用启动不依赖 `release/windows-portable/`、离线 `wheelhouse/` 或内置安装器。

### 运行

```bash
python main.py
```

## 主要特性

- 一级导航拆分为文档工作台、图片工作台和设置页
- 文档、PDF、图片、OCR、去水印任务支持文件池、任务队列和执行日志
- 支持检测 LibreOffice、Pandoc、Poppler、Tesseract、FFmpeg、PyMuPDF、pypdf、python-docx 和 openpyxl
- 支持拖拽导入图片
- 图片工作台保留常驻画布和右侧控制面板
- 支持撤销与重做
- 网格变形与透视变换支持实时预览
- 导出前后增强预览
- 导出支持后台进度、预计剩余时间和取消
- 支持 OpenCV 超分模型下载与本地模型使用

## 文档工作台

文档工作台提供本地文件任务队列：

- 文档转换：Office 转 PDF、PPT 转图片、Markdown / HTML / TXT 转换、表格转 CSV
- PDF 工具：转图片、拆分、合并、压缩、旋转、加密、解密、OCR 文本提取和文字水印处理
- 图片工具：图片转 PDF、格式互转、压缩、裁剪、缩放和批量处理
- OCR 任务：图片 / PDF 转 TXT、DOCX、XLSX 或可搜索 PDF
- 去水印任务：PDF 文本水印删除，以及部分图片修复和背景填充操作

部分能力依赖本机命令行工具。应用会在文档工作台和设置页展示本地后端检测状态。

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

## 可选本地后端

Python 依赖通过 `requirements.txt` 安装。部分文档工作流会在存在时调用外部工具：

- LibreOffice / `soffice`：Office 转换
- Pandoc：Markdown / HTML / TXT 等标记文档转换
- Poppler 工具，如 `pdftoppm` 和 `pdfinfo`：PDF 转图片
- Tesseract：OCR 回退识别
- FFmpeg：预留给后续媒体相关扩展

## 仓库结构

```text
FrameMorph-python/
├── main.py
├── config/
├── core/
├── ui/
├── utils/
├── docs/
├── assets/
│   └── screenshots/
├── models/
│   └── opencv_dnn_superres/
├── scripts/
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

当前版本：`0.2.0`

详见 [VERSION](VERSION)。

## 许可证

MIT License，详见 [LICENSE](LICENSE)。第三方库、命令行工具和模型文件遵循其各自许可证。
