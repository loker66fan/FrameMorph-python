# Project Summary

## Name

FrameMorph-python

## One-line Description

A desktop image editor for practical image transformation, annotation, and high-resolution export workflows.

## Short Description

FrameMorph-python is the repository for the desktop application `形绘`, built with PySide6, Pillow, and OpenCV. It provides a canvas-first workflow for loading images, applying geometric edits, placing text overlays, previewing enhancement results, and exporting high-resolution outputs.

## Core Value

- Keep the editing workflow local and responsive
- Expose practical transform tools without requiring external services
- Provide multiple export enhancement paths for different quality / speed tradeoffs

## Main Features

- Crop with freeform and fixed ratios
- Resize, stretch, and rotate
- Mesh warp
- Perspective correction
- Text overlay management
- High-resolution export
- Export progress, ETA, and cancel
- OpenCV super-resolution model management

## Target Users

- Users who need a lightweight local image editing utility
- People preparing screenshots, document images, posters, or edited exports
- Developers or power users who want inspectable Python code and local model support

## Technical Highlights

- PySide6 desktop UI
- QGraphicsView-based canvas interaction
- Pillow-based image pipeline
- OpenCV-based perspective and super-resolution support
- Background export thread with progress reporting
- Thumbnail-first export preview optimization with cache reuse

## Repository Status

- Active local development
- Basic release materials included
- Documentation available for maintenance and end-user operation

## Related Files

- [README.md](README.md)
- [docs/TECHNICAL.md](docs/TECHNICAL.md)
- [docs/USER_GUIDE.md](docs/USER_GUIDE.md)
- [VERSION](VERSION)
