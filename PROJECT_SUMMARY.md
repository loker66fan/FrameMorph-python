# Project Summary

## Name

FrameMorph-python

## One-line Description

A local desktop toolkit for image editing, document conversion, PDF processing, OCR workflows, and high-resolution export.

## Short Description

FrameMorph-python is the repository for the desktop application `形绘`, built with PySide6, Pillow, OpenCV, PyMuPDF, pypdf, python-docx, and openpyxl. It combines a document workbench for local file processing with an image workbench for canvas-based editing, enhancement preview, and high-resolution export.

## Core Value

- Keep file processing and image editing local and inspectable
- Provide practical batch workflows for documents, PDFs, images, OCR, and watermark-related tasks
- Preserve the existing canvas-first image editor with multiple export enhancement paths
- Make runtime backend availability visible before users start conversion tasks

## Main Features

- Document workbench with file pool, task queue, execution log, and output directory handling
- Office / markup conversion routes, including Office to PDF, PPT to images, markup conversion, and spreadsheet to CSV
- PDF tools for image export, split, merge, compression, rotation, encryption, decryption, OCR text extraction, and text watermark handling
- Image batch tasks for PDF conversion, format conversion, compression, crop, resize, and batch processing
- OCR routes for image / PDF to TXT, DOCX, XLSX, or searchable PDF
- Settings page for theme, font size, default output directory, and local backend detection
- Crop with freeform and fixed ratios
- Resize, stretch, and rotate
- Mesh warp
- Perspective correction
- Text overlay management
- High-resolution export
- Export progress, ETA, and cancel
- OpenCV super-resolution model management

## Target Users

- Users who need a local desktop utility for documents, PDFs, images, OCR, and edited exports
- People preparing screenshots, document images, PDFs, posters, or batch conversion outputs
- Developers or power users who want inspectable Python code and local model support

## Technical Highlights

- PySide6 desktop UI
- First-level navigation for document workbench, image workbench, and settings
- QThread-based document task runner with structured task errors
- QGraphicsView-based canvas interaction
- Pillow-based image pipeline
- OpenCV-based perspective and super-resolution support
- PyMuPDF and pypdf-backed PDF operations
- python-docx and openpyxl-backed document output helpers
- External backend detection for LibreOffice, Pandoc, Poppler, Tesseract, and FFmpeg
- Background export thread with progress reporting
- Thumbnail-first export preview optimization with cache reuse

## Repository Status

- Active local development
- Release materials updated for version 0.2.0
- Screenshot assets included for document, image, export, mesh warp, and settings pages
- Documentation available for maintenance, release publishing, packaging, and end-user operation

## Related Files

- [README.md](README.md)
- [docs/TECHNICAL.md](docs/TECHNICAL.md)
- [docs/USER_GUIDE.md](docs/USER_GUIDE.md)
- [VERSION](VERSION)
- [CHANGELOG.md](CHANGELOG.md)
