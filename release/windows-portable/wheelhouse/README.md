# Windows Wheelhouse

Place offline Windows wheel files in this folder before moving the project to a computer without internet access.

Recommended way to populate this folder on a machine with internet:

```bash
python scripts/prepare_windows_offline_wheels.py
```

That script downloads the Windows `cp311` wheels required by:

- `release/windows-portable/requirements-windows-build.txt`

Once the wheelhouse has been prepared, copy the entire repository to the offline Windows machine and run:

```bat
release\windows-portable\build_windows.bat
```

The build script will automatically prefer these local wheel files and install them with `--no-index`.

Notes:

- This folder is meant for transferred build dependencies, not for runtime output.
- Optional PyTorch SRCNN support is not included in the default offline wheel set because it would make the package much larger.
