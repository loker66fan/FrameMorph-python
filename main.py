import faulthandler

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main() -> int:
    faulthandler.enable()
    app = QApplication([])
    app.setApplicationName("形绘")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
