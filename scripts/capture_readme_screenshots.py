from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.main_window import MainWindow


OUTPUT_DIR = ROOT / "assets" / "screenshots"
SAMPLE_IMAGE = OUTPUT_DIR / "_sample_input.png"


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


def capture_window(window: MainWindow, output_path: Path) -> None:
    window.repaint()
    QApplication.processEvents()
    pixmap = window.grab()
    pixmap.save(str(output_path))


def main() -> int:
    app = QApplication([])
    app.setApplicationName("形绘 Screenshot Capture")

    create_sample_image(SAMPLE_IMAGE)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    window = MainWindow()
    window.resize(1640, 980)
    window.show()
    window.load_image(str(SAMPLE_IMAGE))
    QApplication.processEvents()

    def run_capture() -> None:
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

        window.close()
        app.quit()

    QTimer.singleShot(0, run_capture)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
