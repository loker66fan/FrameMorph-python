# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, adapted for this repository's current development style.

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
