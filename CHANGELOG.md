# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, adapted for this repository's current development style.

## [0.2.0] - 2026-05-20

### Added

- Document workbench with module navigation for document conversion, PDF tools, image tasks, OCR, and watermark workflows
- Batch task queue with file pool management, task status tracking, execution logs, and default output directory support
- Local document processing backends for Office / markup conversion, PDF split / merge / compression / rotation / encryption, OCR export, image conversion, and selected watermark operations
- Settings page for theme, font size, default output directory, and runtime dependency status
- Region selection helpers for image repair and watermark-related workflows
- Release screenshots for document workbench and settings page

### Changed

- Split the main application into document workbench, image workbench, and settings navigation entries
- Updated repository positioning from a single image editor to a local file and image processing desktop toolkit
- Updated README, project summary, release metadata, screenshot documentation, and packaging notes for the expanded feature set
- Improved screenshot capture script so it creates `QApplication` before importing window UI code and captures the new workbench pages
- Added a startup guard for PyQt / PySide Fluent Widgets namespace conflicts
- Updated runtime dependencies to include PDF, Office document, spreadsheet, and OCR-adjacent Python libraries

### Notes

- Project license remains MIT.
- Third-party libraries and external tools keep their own licenses and installation requirements.
- Some document features depend on local command-line tools such as LibreOffice, Pandoc, Poppler, Tesseract, or FFmpeg.

## [0.1.0] - 2026-05-03

### Added

- Initial desktop image editing workflow based on `PySide6`
- Image loading through file picker and drag-and-drop
- Crop panel with freeform and fixed ratio crop
- Transform panel with resize, stretch, and rotate support
- Mesh warp workflow
- Perspective correction workflow
- Text overlay management
- High-resolution export pipeline
- OpenCV `dnn_superres` model selection and local model support
- OpenCV model download support for supported super-resolution models
- Export progress dialog with percentage, ETA, and cancel support
- Technical maintenance documentation
- User guide documentation
- English repository README
- Project summary for release and repository description reuse
- License and version files

### Changed

- Refactored export support logic into `ui/export_support.py`
- Refactored export UI and export workflow logic into `ui/export_mixin.py`
- Optimized export preview by using thumbnail-first enhancement and preview cache reuse
- Reworked export comparison preview into a more stable vertical layout
- Improved `dnn_superres` error handling with model / scale mismatch detection
- Improved right-side control panel scrolling and readability

### Fixed

- Export preview overlap issues
- Export panel overflow usability issues
- Better model mismatch reporting for OpenCV super-resolution workflows

### Notes

- This is the first structured release version prepared for repository publication.
- Screenshot assets are documented but still need real captured images for final repository presentation.
