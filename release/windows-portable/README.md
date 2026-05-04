# Windows Portable Build

This folder contains the files needed to build a Windows `.exe` release of FrameMorph-python.

## Goal

Generate a distributable Windows build that can be opened on other Windows devices without requiring Python to be installed manually.

## Important Note

Windows `.exe` builds should be produced on a Windows environment for the most reliable result.

Recommended options:

1. Build directly on a Windows machine
2. Build inside a clean Windows VM
3. Use GitHub Actions with a Windows runner

## Included Files

- `build_windows.bat`
  - one-click Windows build script
- `FrameMorph-python.spec`
  - PyInstaller spec file
- `README.md`
  - this guide

## Build Steps on Windows

1. Install Python 3.11+
2. Open PowerShell or CMD in the project root
3. Run:

```bat
release\windows-portable\build_windows.bat
```

The script now:

- shows a clear `BUILD SUCCESS` or `BUILD FAILED` message
- prints output paths on success
- prints the failure reason on error
- waits for a key press before closing
- creates an isolated `.build-venv` before packaging to avoid polluted global Python environments

## Expected Output

The final Windows build will be generated under:

```text
dist\FrameMorph-python\
```

or as configured by the spec/build script.

The build script will also copy the final result into:

```text
release\windows-build-output\FrameMorph-python\
```

and generate:

```text
release\windows-build-output\FrameMorph-python-windows-portable.zip
```

## What Gets Bundled

- application code
- required Python runtime
- models folder
- assets folder
- documentation files selected in the build script/spec

## Distribution Recommendation

For sharing to other Windows devices:

1. Build on Windows
2. Compress the generated `dist\FrameMorph-python\` folder
3. Send the compressed folder to the target device
4. Extract and run `FrameMorph-python.exe`

## If You Want a Single EXE

You can switch to one-file mode later, but one-folder mode is more stable for Qt + OpenCV + model assets.
