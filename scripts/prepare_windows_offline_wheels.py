from __future__ import annotations

import argparse
import subprocess
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REQUIREMENTS = ROOT / "release" / "windows-portable" / "requirements-windows-build.txt"
DEFAULT_DESTINATION = ROOT / "release" / "windows-portable" / "wheelhouse"
DEFAULT_INSTALLER_DIR = ROOT / "release" / "windows-portable" / "python-installer"
PYTHON_INSTALLER_NAME = "python-3.11.9-amd64.exe"
PYTHON_INSTALLER_URL = f"https://www.python.org/ftp/python/3.11.9/{PYTHON_INSTALLER_NAME}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download Windows build wheels for offline FrameMorph-python packaging."
    )
    parser.add_argument(
        "--requirements",
        type=Path,
        default=DEFAULT_REQUIREMENTS,
        help=f"Requirements file to download from. Default: {DEFAULT_REQUIREMENTS}",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=DEFAULT_DESTINATION,
        help=f"Wheel output directory. Default: {DEFAULT_DESTINATION}",
    )
    parser.add_argument(
        "--platform",
        default="win_amd64",
        help="Target wheel platform. Default: win_amd64",
    )
    parser.add_argument(
        "--python-version",
        default="3.11",
        help="Target Python version for wheel resolution. Default: 3.11",
    )
    parser.add_argument(
        "--installer-dest",
        type=Path,
        default=DEFAULT_INSTALLER_DIR,
        help=f"Bundled Python installer output directory. Default: {DEFAULT_INSTALLER_DIR}",
    )
    parser.add_argument(
        "--skip-python-installer",
        action="store_true",
        help="Skip downloading the official offline Windows Python installer.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    requirements = args.requirements.resolve()
    destination = args.dest.resolve()
    installer_destination = args.installer_dest.resolve()

    if not requirements.exists():
        print(f"Missing requirements file: {requirements}", file=sys.stderr)
        return 1

    destination.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "pip",
        "download",
        "--dest",
        str(destination),
        "--only-binary=:all:",
        "--platform",
        args.platform,
        "--python-version",
        args.python_version,
        "--implementation",
        "cp",
        "-r",
        str(requirements),
    ]

    print("Downloading Windows wheels for offline packaging...")
    print(" ".join(command))
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode != 0:
        return completed.returncode

    if not args.skip_python_installer:
        installer_destination.mkdir(parents=True, exist_ok=True)
        installer_path = installer_destination / PYTHON_INSTALLER_NAME
        if installer_path.exists():
            print()
            print(f"Python installer already exists: {installer_path}")
        else:
            print()
            print(f"Downloading bundled Python installer from {PYTHON_INSTALLER_URL}")
            request = urllib.request.Request(
                PYTHON_INSTALLER_URL,
                headers={"User-Agent": "FrameMorph-python-offline-prep"},
            )
            with urllib.request.urlopen(request, timeout=120) as response, installer_path.open("wb") as file:
                while True:
                    chunk = response.read(1024 * 256)
                    if not chunk:
                        break
                    file.write(chunk)
            print(f"Saved Python installer: {installer_path}")

    print()
    print("Wheel download completed.")
    print(f"Wheelhouse: {destination}")
    if not args.skip_python_installer:
        print(f"Bundled Python installer: {installer_destination / PYTHON_INSTALLER_NAME}")
    print("Copy the full repository to the offline Windows machine.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
