# 仓库发布信息

本文件用于整理 GitHub 仓库发布时最常用的元信息，便于直接复制使用。

## 1. GitHub About 文案

### 中文短简介

基于 PySide6、Pillow 和 OpenCV 的桌面图像编辑工具，支持裁剪、缩放、网格变形、透视矫正、文字图层和高清导出。

### 英文短简介

A desktop image editor built with PySide6, Pillow, and OpenCV for crop, transform, mesh warp, perspective correction, text overlays, and high-resolution export.

## 2. GitHub 仓库标题建议

### 中文

FrameMorph-python - 形绘桌面图像编辑工具

### 英文

FrameMorph-python - Desktop Image Editor with PySide6, Pillow, and OpenCV

## 3. GitHub Topics 建议

建议 topics：

- python
- pyside6
- qt
- pillow
- opencv
- image-editor
- desktop-app
- image-processing
- super-resolution
- qgraphicsview

## 4. GitHub Release 标题模板

### 英文

`v0.1.0 - Initial public release`

### 中文

`v0.1.0 - 首个公开发布版本`

## 5. GitHub Release Notes 模板

### English

```markdown
## Highlights

- Crop, resize, stretch, rotate, mesh warp, and perspective correction
- Text overlay workflow
- High-resolution export with multiple enhancement paths
- OpenCV dnn_superres model support
- Background export with progress, ETA, and cancel support

## Internal improvements

- Export logic extracted into dedicated modules
- Thumbnail-first export preview optimization
- Improved model mismatch diagnostics
- Technical and user documentation added

## Notes

- This release is prepared as the first public repository version.
- Screenshot placeholders are documented; real screenshots can be added later under `assets/screenshots/`.
```

### 中文

```markdown
## 版本亮点

- 支持裁剪、缩放、拉伸、旋转、网格变形、透视矫正
- 支持文字图层
- 支持高清导出与多种增强路径
- 支持 OpenCV dnn_superres 模型
- 支持后台导出、进度、预计剩余时间与取消

## 内部优化

- 导出逻辑拆分为独立模块
- 导出预览改为缩略图优先并加入缓存
- 增强了模型不匹配时的错误提示
- 补充了技术文档和使用文档

## 备注

- 当前版本适合作为首个公开仓库版本
- 截图目录已准备好，后续可补充真实截图资源
```

## 6. 仓库摘要文案

### 中文

FrameMorph-python 是桌面应用“形绘”的项目仓库。形绘采用 PySide6、Pillow 与 OpenCV 构建，面向实际编辑需求，提供裁剪、变换、网格变形、透视矫正、文字叠加以及高清导出能力，并支持 OpenCV 超分模型管理与后台导出进度反馈。

### English

FrameMorph-python is the repository for the desktop application `形绘`, built with PySide6, Pillow, and OpenCV. It focuses on practical editing workflows, including crop, transform, mesh warp, perspective correction, text overlay, and high-resolution export, with OpenCV super-resolution model support and background export progress reporting.

## 7. 截图建议

建议准备以下仓库截图：

- `workbench.png`
  - 展示主工作台、画布和右侧控制栏
- `export-panel.png`
  - 展示导出增强、模型选择和前后预览
- `mesh-warp.png`
  - 展示网格变形交互

建议截图要求：

- 统一语言
- 统一窗口尺寸
- 尽量使用清晰的示例图片
- 避免出现隐私内容

## 8. 当前发布文件

当前仓库已具备：

- `README.md`
- `LICENSE`
- `VERSION`
- `CHANGELOG.md`
- `PROJECT_SUMMARY.md`
- `docs/TECHNICAL.md`
- `docs/USER_GUIDE.md`
- `assets/screenshots/README.md`
