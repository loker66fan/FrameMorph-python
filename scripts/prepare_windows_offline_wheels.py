from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REQUIREMENTS = ROOT / "release" / "windows-portable" / "requirements-windows-build.txt"
DEFAULT_DESTINATION = ROOT / "release" / "windows-portable" / "wheelhouse"


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
    return parser


def main() -> int:
    args = build_parser().parse_args()
    requirements = args.requirements.resolve()
    destination = args.dest.resolve()

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

    print()
    print("Wheel download completed.")
    print(f"Wheelhouse: {destination}")
    print("Copy the full repository, including release/windows-portable/wheelhouse, to the offline Windows machine.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
