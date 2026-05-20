# 仓库发布信息

本文件用于整理 GitHub 仓库发布时最常用的元信息，便于直接复制使用。

## 1. GitHub About 文案

### 中文短简介

基于 PySide6、Pillow、OpenCV 和 Python 文档处理库的本地桌面工具，支持图片编辑、文档转换、PDF 处理、OCR 工作流和高清导出。

### 英文短简介

A local desktop toolkit built with PySide6, Pillow, OpenCV, and Python document libraries for image editing, document conversion, PDF processing, OCR workflows, and high-resolution export.

## 2. GitHub 仓库标题建议

### 中文

FrameMorph-python - 形绘桌面图像编辑工具

FrameMorph-python - 形绘本地文件处理工具

### 英文

FrameMorph-python - Local File and Image Processing Toolkit

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
- pdf-tools
- document-conversion
- ocr
- offline-first

## 4. GitHub Release 标题模板

### 英文

`v0.2.0 - Document workbench and release metadata refresh`

### 中文

`v0.2.0 - 文档工作台与发布资料更新`

## 5. GitHub Release Notes 模板

### English

```markdown
## Highlights

- Added Document Workbench for document conversion, PDF tools, image tasks, OCR routes, and watermark workflows
- Added file pool, batch task queue, status tracking, execution logs, and configurable output directory
- Added Settings page for theme, font size, output directory, and local backend status
- Kept the Image Workbench for crop, transform, mesh warp, perspective correction, text overlays, and high-resolution export
- Added release screenshots for document workbench and settings page

## Internal improvements

- Updated runtime dependency list for PDF, Office document, spreadsheet, and OCR-adjacent workflows
- Updated screenshot capture script to initialize `QApplication` before importing UI code
- Updated README, project summary, release metadata, screenshot documentation, and packaging notes
- Preserved MIT license; third-party libraries and external tools keep their own licenses

## Notes

- Some document features depend on local tools such as LibreOffice, Pandoc, Poppler, Tesseract, or FFmpeg.
- Screenshot assets are available under `assets/screenshots/`.
```

### 中文

```markdown
## 版本亮点

- 新增文档工作台，覆盖文档转换、PDF 工具、图片任务、OCR 路线和去水印工作流
- 新增文件池、批量任务队列、状态跟踪、执行日志和可配置输出目录
- 新增设置页，支持主题、字体大小、输出目录和本地后端状态管理
- 保留图片工作台，支持裁剪、变换、网格、透视、文字图层和高清导出
- 新增文档工作台与设置页截图资源

## 内部优化

- 更新运行时依赖，覆盖 PDF、Office 文档、表格和 OCR 相关 Python 库
- 修复截图脚本初始化顺序，确保先创建 `QApplication` 再导入 UI 代码
- 更新 README、项目简介、发布元信息、截图说明和打包说明
- 许可证保持 MIT；第三方库和外部工具遵循其各自许可证

## 备注

- 部分文档能力依赖 LibreOffice、Pandoc、Poppler、Tesseract 或 FFmpeg 等本地工具
- 截图资源已放入 `assets/screenshots/`
```

## 6. 仓库摘要文案

### 中文

FrameMorph-python 是桌面应用“形绘”的项目仓库。形绘采用 PySide6、Pillow、OpenCV、PyMuPDF、pypdf、python-docx 和 openpyxl 构建，面向本地文件处理与图片编辑需求，提供文档转换、PDF 工具、OCR 工作流、去水印任务、画布编辑和高清导出能力。

### English

FrameMorph-python is the repository for the desktop application `形绘`, built with PySide6, Pillow, OpenCV, PyMuPDF, pypdf, python-docx, and openpyxl. It focuses on local file processing and image editing workflows, including document conversion, PDF tools, OCR routes, watermark tasks, canvas editing, and high-resolution export.

## 7. 截图建议

建议准备以下仓库截图：

- `workbench.png`
  - 展示图片工作台、画布和右侧控制栏
- `document-workbench.png`
  - 展示文档工作台、模块导航、文件池和任务队列
- `export-panel.png`
  - 展示导出增强、模型选择和前后预览
- `mesh-warp.png`
  - 展示网格变形交互
- `settings-page.png`
  - 展示主题、字体、输出目录和环境检测设置

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
- `docs/PACKAGING.md`
- `scripts/capture_readme_screenshots.py`
- `assets/screenshots/README.md`
