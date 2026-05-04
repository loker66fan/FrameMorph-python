# Windows Build Output

This folder is the mirrored release output location after a successful Windows build.

## Expected Build Output

### Portable folder

```text
release/windows-build-output/FrameMorph-python/
```

This folder will contain the runnable Windows application bundle, including:

- `FrameMorph-python.exe`
- bundled Python runtime
- required dependencies
- assets
- models
- docs

Important:

- do not run only `FrameMorph-python.exe` after separating it from this folder
- the whole folder must stay intact
- alternatively, send and extract `FrameMorph-python-windows-portable.zip`

### Portable zip package

```text
release/windows-build-output/FrameMorph-python-windows-portable.zip
```

Example:

```text
release/windows-build-output/FrameMorph-python-windows-portable.zip
```

## Original PyInstaller Output

The raw PyInstaller output still exists under:

```text
dist/FrameMorph-python/
```

## How To Produce It

### Option 1: On a Windows machine

Run:

```bat
release\windows-portable\build_windows.bat
```

### Option 2: On GitHub Actions

Run the workflow:

```text
Windows Portable Build
```

The GitHub artifact is uploaded from `dist/`, but local Windows builds now also copy the final result into `release/windows-build-output/`.

The Windows build script now explicitly checks that:

- `dist/FrameMorph-python/` exists
- `release/windows-build-output/FrameMorph-python/` is copied successfully
- `FrameMorph-python.exe` exists after copy

## Current Status

This repository already contains:

- the PyInstaller spec
- the Windows build script
- the GitHub Actions workflow
- release documentation

But the final Windows `.exe` must still be produced in a Windows build environment.
