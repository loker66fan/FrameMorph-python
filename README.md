# FrameMorph-python

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](requirements.txt)
[![UI](https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt&logoColor=white)](README.md)
[![License](https://img.shields.io/badge/License-MIT-black)](LICENSE)
[![Windows Portable Build](https://github.com/loker66fan/FrameMorph-python/actions/workflows/windows-portable-build.yml/badge.svg)](https://github.com/loker66fan/FrameMorph-python/actions/workflows/windows-portable-build.yml)

A desktop image editor for practical local workflows, built with `PySide6`, `Pillow`, `OpenCV`, and `NumPy`.

[中文说明 / Chinese README](README.zh-CN.md)

`FrameMorph-python` is the repository name. `形绘` is the desktop application name shown to end users.

## Overview

This project is built for hands-on image editing on a local machine rather than cloud-first or template-heavy workflows.

- crop with fixed ratios or free selection
- resize, stretch, and rotate
- mesh warp and perspective correction
- text overlays on the canvas
- high-resolution export
- multiple enhancement paths, including OpenCV `dnn_superres`

## Screenshots

| Workbench | Mesh Warp | Export Panel |
| --- | --- | --- |
| ![Workbench](assets/screenshots/workbench.png) | ![Mesh Warp](assets/screenshots/mesh-warp.png) | ![Export Panel](assets/screenshots/export-panel.png) |

## Quick Start

### Requirements

- Python 3.11+

### Install

```bash
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

## Highlights

- Drag-and-drop image loading
- Persistent right-side control panels with a visible canvas workspace
- Undo and redo support
- Real-time preview for mesh warp and perspective transform
- Export comparison preview before and after enhancement
- Background export with progress, ETA, and cancel support
- OpenCV super-resolution model download support

## Enhancement and Export

The export workflow currently supports three enhancement routes:

1. Built-in classic super-resolution enhancement
2. PyTorch SRCNN with a custom local model path
3. OpenCV `dnn_superres`

Supported OpenCV model families:

- EDSR
- ESPCN
- FSRCNN
- LapSRN

The application can:

- auto-detect model type and scale from `.pb` filenames
- download supported OpenCV models into `models/opencv_dnn_superres/`
- show export progress with percentage and estimated remaining time

## Repository Layout

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

## Documentation

- Technical maintenance guide: [docs/TECHNICAL.md](docs/TECHNICAL.md)
- User guide: [docs/USER_GUIDE.md](docs/USER_GUIDE.md)
- Release metadata guide: [docs/RELEASE.md](docs/RELEASE.md)
- Packaging guide: [docs/PACKAGING.md](docs/PACKAGING.md)
- GitHub Actions Windows build: [docs/GITHUB_ACTIONS_WINDOWS_BUILD.md](docs/GITHUB_ACTIONS_WINDOWS_BUILD.md)
- Chinese release guide: [docs/RELEASE.zh-CN.md](docs/RELEASE.zh-CN.md)
- Project summary: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)
- Windows portable build folder: [release/windows-portable](release/windows-portable)

## Version

Current version: `0.1.0`

See [VERSION](VERSION).

## License

MIT License. See [LICENSE](LICENSE).
