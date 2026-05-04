from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "release" / "offline-packages"

EXCLUDE_PARTS = {
    ".git",
    ".build-venv",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".codex",
    "build",
    "dist",
}
EXCLUDE_PREFIXES = (
    Path("release/windows-build-output"),
    Path("release/offline-packages"),
    Path("release/windows-portable/python-runtime"),
)
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".part"}


def should_skip(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDE_PARTS for part in rel.parts):
        return True
    if any(rel == prefix or prefix in rel.parents for prefix in EXCLUDE_PREFIXES):
        return True
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    return False


def main() -> int:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = OUTPUT_DIR / f"FrameMorph-python-offline-windows-packaging-{version}.zip"
    if zip_path.exists():
        zip_path.unlink()

    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED, compresslevel=6) as zf:
        for path in ROOT.rglob("*"):
            if path.is_dir() or should_skip(path):
                continue
            zf.write(path, path.relative_to(ROOT).as_posix())

    print(zip_path)
    print(zip_path.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
