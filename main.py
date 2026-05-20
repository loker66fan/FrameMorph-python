import faulthandler
import contextlib
import io
import sys

from PySide6.QtWidgets import QApplication


def has_pyqt_fluent_namespace_conflict() -> bool:
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            import qfluentwidgets
    except Exception:
        return False
    description = qfluentwidgets.__doc__ or ""
    return "PyQt-Fluent-Widgets" in description or "based on PyQt5" in description


def main() -> int:
    if sys.stderr is not None:
        faulthandler.enable(sys.stderr)
    if has_pyqt_fluent_namespace_conflict():
        print(
            "当前 Python 环境中的 qfluentwidgets 命名空间来自 PyQt-Fluent-Widgets，"
            "但本项目使用 PySide6。请使用 PySide6-Fluent-Widgets 环境运行。",
            file=sys.stderr,
        )
        return 2

    app = QApplication([])
    app.setApplicationName("形绘")
    from core.app_settings import apply_app_appearance, load_app_settings
    load_app_settings()
    apply_app_appearance(app)
    from ui.main_window import MainWindow

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
