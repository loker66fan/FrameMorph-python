from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


OUTPUT_DIR = ROOT / "assets" / "screenshots"
SAMPLE_IMAGE = OUTPUT_DIR / "_sample_input.png"


def load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def create_sample_image(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1280, 840), "#f5efe3")
    draw = ImageDraw.Draw(image)

    draw.rectangle((70, 90, 1210, 760), fill="#fbf8f2", outline="#d4c6a8", width=4)
    draw.rounded_rectangle((120, 140, 560, 700), radius=26, fill="#dbe8f5", outline="#7ea3c6", width=5)
    draw.rounded_rectangle((640, 170, 1130, 640), radius=42, fill="#f3d2a2", outline="#b36f37", width=6)
    draw.polygon([(780, 235), (1065, 220), (1110, 475), (750, 560)], fill="#f7e4c6", outline="#7c4d20")
    draw.ellipse((205, 230, 470, 500), fill="#b6d1ec", outline="#537b9e", width=5)
    draw.line((180, 620, 1040, 650), fill="#8d6e63", width=10)
    draw.text((150, 150), "形绘 Demo", fill="#21415c")
    draw.text((695, 605), "Export Preview Sample", fill="#6a3d13")

    image.save(path)


def draw_text(draw: ImageDraw.ImageDraw, position: tuple[int, int], text: str, size: int, fill: str) -> None:
    draw.text(position, text, font=load_font(size), fill=fill)


def create_fallback_screen(path: Path, title: str, subtitle: str, cards: list[tuple[str, list[str]]]) -> None:
    if path.exists():
        return

    width, height = 1640, 980
    image = Image.new("RGB", (width, height), "#f4f7fb")
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, 86, height), fill="#eef3f8")
    for index, label in enumerate(["Docs", "Image", "Settings"]):
        y = 110 + index * 86
        fill = "#dfeaf7" if label in title else "#f8fbff"
        draw.rounded_rectangle((18, y, 68, y + 50), radius=12, fill=fill, outline="#c7d6e6")
        draw_text(draw, (24, y + 17), label[:3], 13, "#31506f")

    draw.rounded_rectangle((118, 36, width - 42, 176), radius=18, fill="#ffffff", outline="#d7dfeb", width=2)
    draw_text(draw, (150, 68), title, 34, "#17324d")
    draw_text(draw, (150, 116), subtitle, 18, "#61758a")

    left = 118
    top = 210
    card_width = 450
    card_height = 260
    gap = 28

    for index, (card_title, lines) in enumerate(cards):
        col = index % 3
        row = index // 3
        x = left + col * (card_width + gap)
        y = top + row * (card_height + gap)
        draw.rounded_rectangle((x, y, x + card_width, y + card_height), radius=18, fill="#ffffff", outline="#d7dfeb", width=2)
        draw_text(draw, (x + 28, y + 26), card_title, 24, "#17324d")
        for line_index, line in enumerate(lines):
            line_y = y + 78 + line_index * 34
            draw.rounded_rectangle((x + 28, line_y + 4, x + 42, line_y + 18), radius=4, fill="#6a9bd8")
            draw_text(draw, (x + 58, line_y), line, 17, "#40556b")

    image.save(path)


def create_fallback_screenshots() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    create_sample_image(SAMPLE_IMAGE)
    create_fallback_screen(
        OUTPUT_DIR / "document-workbench.png",
        "Document Workbench",
        "Local conversion queue for documents, PDFs, images, OCR, and watermark tasks.",
        [
            ("Modules", ["Document conversion", "PDF tools", "Image tasks", "OCR routes"]),
            ("File Pool", ["Drag files or folders", "Filter by module", "Queue selected items"]),
            ("Task Queue", ["Waiting / running / done", "Batch execution", "Detailed error logs"]),
            ("Backends", ["LibreOffice / Pandoc", "Poppler / Tesseract", "PyMuPDF / pypdf"]),
            ("Output", ["Configurable directory", "Task grouped folders", "Open result location"]),
        ],
    )
    create_fallback_screen(
        OUTPUT_DIR / "settings-page.png",
        "Settings",
        "Appearance, default output directory, and local backend status.",
        [
            ("Appearance", ["Light / dark theme", "Small / standard / large font", "Saved locally"]),
            ("Files", ["Default output directory", "Open output folder", "Used by task queue"]),
            ("Environment", ["Refresh backend status", "Check document tools", "Check OCR / PDF tools"]),
        ],
    )


def has_pyqt_fluent_namespace_conflict() -> bool:
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            import qfluentwidgets
    except Exception:
        return False
    description = qfluentwidgets.__doc__ or ""
    return "PyQt-Fluent-Widgets" in description or "based on PyQt5" in description


def capture_window(window, output_path: Path) -> None:
    window.repaint()
    QApplication.processEvents()
    pixmap = window.grab()
    pixmap.save(str(output_path))


def main() -> int:
    if has_pyqt_fluent_namespace_conflict():
        create_fallback_screenshots()
        return 0

    app = QApplication([])
    app.setApplicationName("形绘 Screenshot Capture")

    from core.app_settings import apply_app_appearance, load_app_settings
    from ui.main_window import MainWindow

    load_app_settings()
    apply_app_appearance(app)

    create_sample_image(SAMPLE_IMAGE)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    window = MainWindow()
    window.resize(1640, 980)
    window.show()
    QApplication.processEvents()

    def run_capture() -> None:
        window.switchTo(window.document_workbench)
        window.document_workbench._ingest_paths([str(SAMPLE_IMAGE)])
        QApplication.processEvents()
        capture_window(window, OUTPUT_DIR / "document-workbench.png")

        window.switchTo(window.image_workbench)
        window.load_image(str(SAMPLE_IMAGE))
        QApplication.processEvents()

        window._activate_panel("crop")
        QApplication.processEvents()
        capture_window(window, OUTPUT_DIR / "workbench.png")

        window._activate_panel("mesh")
        window._rebuild_mesh_overlay()
        QApplication.processEvents()
        capture_window(window, OUTPUT_DIR / "mesh-warp.png")

        window._activate_panel("export")
        window.export_enhance_switch.setChecked(True)
        window.export_dnn_radio.setChecked(True)
        cache_model = ROOT / "models" / "opencv_dnn_superres" / "EDSR_x4.pb"
        if cache_model.exists():
            window.export_dnn_model_path.setPlainText(str(cache_model))
            window._apply_dnn_model_guess_from_path(str(cache_model))
        window.update_export_comparison_preview()
        QApplication.processEvents()
        capture_window(window, OUTPUT_DIR / "export-panel.png")

        window.switchTo(window.settings_page)
        QApplication.processEvents()
        capture_window(window, OUTPUT_DIR / "settings-page.png")

        window.close()
        app.quit()

    QTimer.singleShot(0, run_capture)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
