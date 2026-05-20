# Packaging Guide

## 1. Goal

This document describes a practical baseline packaging workflow for turning FrameMorph-python into a distributable desktop executable for the application `形绘` using PyInstaller.

## 2. Recommended Environment

- Python 3.11+
- Clean virtual environment
- Dependencies installed from `requirements.txt`
- Use `release/windows-portable/requirements-windows-build.txt` only for the Windows packaging flow, since it extends the runtime dependencies with packaging-only tools

## 3. Install Packaging Tool

```bash
pip install pyinstaller
```

For the repository's Windows packaging flow, prefer the dedicated build requirements file:

```text
release/windows-portable/requirements-windows-build.txt
```

## 4. Basic One-file Build

```bash
pyinstaller -F -w main.py -n FrameMorph-python
```

Explanation:

- `-F`
  - build a single-file executable
- `-w`
  - disable console window for GUI mode
- `-n FrameMorph-python`
  - set output application name

## 5. Recommended One-folder Build

For debugging and asset inspection, one-folder mode is often easier:

```bash
pyinstaller -D -w main.py -n FrameMorph-python
```

## 6. Output Location

PyInstaller outputs to:

- `build/`
- `dist/`

The final executable is typically under:

```text
dist/FrameMorph-python/
```

or in one-file mode:

```text
dist/FrameMorph-python
```

## 7. Model Files and Assets

Current repository content includes:

- `models/opencv_dnn_superres/`
- `assets/screenshots/`

Runtime UI also depends on:

- `PySide6-Fluent-Widgets` (`qfluentwidgets`)

Document workflows can also use external command-line tools when present:

- LibreOffice / `soffice`
- Pandoc
- Poppler tools such as `pdftoppm` and `pdfinfo`
- Tesseract OCR
- FFmpeg

If release builds are expected to include built-in model files, make sure they are copied into the packaged output or downloaded after first launch.

For example, if you want to bundle models, use PyInstaller data arguments such as:

```bash
pyinstaller -D -w main.py -n FrameMorph-python \
  --add-data "models:models" \
  --add-data "assets:assets"
```

On Windows, replace `:` with `;` in `--add-data`.

## 8. Recommended Packaging Steps

1. Create a clean virtual environment
2. Install dependencies
3. Run the app locally
4. Generate screenshots if needed
5. Build with PyInstaller
6. Test:
   - document workbench startup
   - settings page startup and output directory display
   - backend status refresh
   - at least one document task that only depends on bundled Python libraries
   - image loading
   - mesh warp
   - perspective transform
   - text overlay
   - export
   - `dnn_superres` model loading

Current repository build script already follows this principle by creating a temporary isolated environment named `.build-venv` on Windows before invoking PyInstaller.

## 9. Offline Windows Packaging

To prepare for a Windows machine without internet access:

1. On a machine with internet, run:

```bash
python scripts/prepare_windows_offline_wheels.py
```

2. Verify that these offline assets exist:

```text
release/windows-portable/wheelhouse/
release/windows-portable/python-installer/python-3.11.9-amd64.exe
```

3. Copy the full repository to the offline Windows machine.
4. Run:

```bat
release\windows-portable\build_windows.bat
```

The current build script assumes the target terminal can already run a usable Python interpreter through `py` or `python`.

If the wrong interpreter is selected, set it explicitly:

```bat
set FRAME_MORPH_PYTHON=C:\Path\To\python.exe
release\windows-portable\build_windows.bat
```

Dependency installation still prefers the local wheelhouse with `--no-index` before attempting any network access.

## 10. Notes About OpenCV and Models

- OpenCV `dnn_superres` requires a compatible OpenCV build
- External `.pb` model files are not embedded automatically unless packaged as data
- If users are expected to download models inside the app, shipping without bundled models is also acceptable

This repository now uses `opencv-contrib-python` so the packaged application keeps `dnn_superres` support.

## 11. Release Checklist

- [ ] `README.md` updated
- [ ] `README.zh-CN.md` updated
- [ ] `VERSION` updated
- [ ] `CHANGELOG.md` updated
- [ ] `LICENSE` included
- [ ] screenshots prepared
- [ ] packaging tested on target OS
- [ ] document workbench smoke-tested in packaged app
- [ ] settings page smoke-tested in packaged app
- [ ] export workflow tested in packaged app

## 12. Future Improvement

If release packaging becomes a regular workflow, consider adding:

- a committed `.spec` file
- a simple build script
- platform-specific packaging notes for Windows / macOS / Linux
