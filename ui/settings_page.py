from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QScrollArea, QSizePolicy, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, CardWidget, ComboBox, PrimaryPushButton, PushButton, SubtitleLabel, isDarkTheme, qconfig, setTheme

from core.app_settings import (
    FONT_SIZE_LABELS,
    SUPPORTED_FONT_SIZE_PRESETS,
    SUPPORTED_THEMES,
    THEME_LABELS,
    FontSizePreset,
    app_config,
    ensure_default_output_directory,
    get_current_theme,
    get_default_output_directory_path,
    get_font_size_preset,
    set_default_output_directory,
    set_font_size_preset,
)
from core.document_tasks import detect_document_backends


class SettingsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._backends = detect_document_backends()

        self._build_ui()
        self._apply_styles()
        self._sync_controls_from_settings()
        self._refresh_backend_status()

        qconfig.themeChangedFinished.connect(self._handle_theme_changed_finished)
        app_config.defaultOutputDirectory.valueChanged.connect(self._handle_output_directory_changed)
        app_config.fontSizePreset.valueChanged.connect(self._handle_font_size_preset_changed)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        header_card = CardWidget()
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(20, 20, 20, 20)
        header_layout.setSpacing(8)
        header_layout.addWidget(SubtitleLabel("设置"))

        summary_label = BodyLabel("统一管理软件主题、字体大小、默认输出目录和基础环境状态。")
        summary_label.setWordWrap(True)
        header_layout.addWidget(summary_label)

        self.status_label = BodyLabel("设置已就绪。")
        self.status_label.setObjectName("settingsStatusLabel")
        self.status_label.setWordWrap(True)
        header_layout.addWidget(self.status_label)
        root.addWidget(header_card)

        content_container = QWidget()
        content_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("settingsScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.verticalScrollBar().setSingleStep(20)
        self.scroll_area.setWidget(content_container)
        root.addWidget(self.scroll_area, 1)

        appearance_card = CardWidget()
        appearance_layout = QVBoxLayout(appearance_card)
        appearance_layout.setContentsMargins(18, 18, 18, 18)
        appearance_layout.setSpacing(12)
        appearance_layout.addWidget(SubtitleLabel("外观"))

        appearance_hint = BodyLabel("主题和字体大小会在本次会话中立即生效，并在下次启动时恢复。")
        appearance_hint.setWordWrap(True)
        appearance_layout.addWidget(appearance_hint)
        self.appearance_hint_label = appearance_hint

        self.theme_combo = ComboBox()
        for theme in SUPPORTED_THEMES:
            self.theme_combo.addItem(THEME_LABELS[theme], userData=theme)
        self.theme_combo.currentIndexChanged.connect(self._handle_theme_combo_changed)
        appearance_layout.addWidget(BodyLabel("主题"))
        appearance_layout.addWidget(self.theme_combo)

        self.font_size_combo = ComboBox()
        for preset in SUPPORTED_FONT_SIZE_PRESETS:
            self.font_size_combo.addItem(FONT_SIZE_LABELS[preset], userData=preset)
        self.font_size_combo.currentIndexChanged.connect(self._handle_font_size_combo_changed)
        appearance_layout.addWidget(BodyLabel("软件字体大小"))
        appearance_layout.addWidget(self.font_size_combo)

        content_layout.addWidget(appearance_card)

        output_card = CardWidget()
        output_layout = QVBoxLayout(output_card)
        output_layout.setContentsMargins(18, 18, 18, 18)
        output_layout.setSpacing(12)
        output_layout.addWidget(SubtitleLabel("文件与输出"))

        self.output_directory_label = BodyLabel("")
        self.output_directory_label.setWordWrap(True)
        output_layout.addWidget(self.output_directory_label)

        output_actions = QHBoxLayout()
        output_actions.setSpacing(10)
        self.choose_output_button = PrimaryPushButton("选择目录")
        self.choose_output_button.clicked.connect(self._choose_output_directory)
        self.open_output_button = PushButton("打开目录")
        self.open_output_button.clicked.connect(self._open_output_directory)
        output_actions.addWidget(self.choose_output_button)
        output_actions.addWidget(self.open_output_button)
        output_layout.addLayout(output_actions)
        content_layout.addWidget(output_card)

        environment_card = CardWidget()
        environment_layout = QVBoxLayout(environment_card)
        environment_layout.setContentsMargins(18, 18, 18, 18)
        environment_layout.setSpacing(12)
        environment_layout.addWidget(SubtitleLabel("环境状态"))

        self.backend_env_label = BodyLabel("")
        self.backend_env_label.setWordWrap(True)
        environment_layout.addWidget(self.backend_env_label)

        self.environment_hint_label = BodyLabel("用于确认当前机器是否具备文档转换、OCR 和 PDF 处理的后端能力。")
        self.environment_hint_label.setWordWrap(True)
        environment_layout.addWidget(self.environment_hint_label)

        environment_actions = QHBoxLayout()
        environment_actions.setSpacing(10)
        self.refresh_backend_button = PushButton("刷新环境")
        self.refresh_backend_button.clicked.connect(self._refresh_backends)
        environment_actions.addWidget(self.refresh_backend_button)
        environment_actions.addStretch(1)
        environment_layout.addLayout(environment_actions)
        content_layout.addWidget(environment_card)
        content_layout.addStretch(1)

    def _apply_styles(self) -> None:
        dark = isDarkTheme()
        status_style = (
            "background-color: #22354a; color: #edf5ff; border: 1px solid #46698b; border-radius: 10px; padding: 10px 12px;"
            if dark
            else "background-color: #eaf2ff; color: #17324d; border: 1px solid #bfd3f2; border-radius: 10px; padding: 10px 12px;"
        )
        hint_style = (
            "background-color: #3a3123; color: #f4dfb4; border: 1px solid #7a6540; border-radius: 10px; padding: 8px 10px;"
            if dark
            else "background-color: #fff7e8; color: #5e3b00; border: 1px solid #f0d6a6; border-radius: 10px; padding: 8px 10px;"
        )
        scroll_style = (
            """
            QScrollArea#settingsScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea#settingsScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 12px;
                margin: 4px 0 4px 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(120, 146, 177, 0.72);
                min-height: 44px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(88, 118, 153, 0.9);
            }
            QScrollBar::handle:vertical:pressed {
                background: rgba(66, 93, 127, 0.96);
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
                background: transparent;
                border: none;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
            }
            """
        )

        self.status_label.setStyleSheet(status_style)
        for label in [
            self.appearance_hint_label,
            self.output_directory_label,
            self.backend_env_label,
            self.environment_hint_label,
        ]:
            label.setStyleSheet(hint_style)
        self.scroll_area.setStyleSheet(scroll_style)
        for button in self.findChildren(PushButton):
            button.setMinimumHeight(36)
        for button in self.findChildren(PrimaryPushButton):
            button.setMinimumHeight(38)

    def _sync_controls_from_settings(self) -> None:
        self._sync_theme_combo()
        self._sync_font_size_combo()
        self._update_output_directory_text()

    def _sync_theme_combo(self) -> None:
        current_theme = get_current_theme()
        self.theme_combo.blockSignals(True)
        for index in range(self.theme_combo.count()):
            if self.theme_combo.itemData(index) == current_theme:
                self.theme_combo.setCurrentIndex(index)
                break
        self.theme_combo.blockSignals(False)

    def _sync_font_size_combo(self) -> None:
        preset = get_font_size_preset()
        self.font_size_combo.blockSignals(True)
        for index in range(self.font_size_combo.count()):
            if self.font_size_combo.itemData(index) == preset:
                self.font_size_combo.setCurrentIndex(index)
                break
        self.font_size_combo.blockSignals(False)

    def _update_output_directory_text(self) -> None:
        output_dir = get_default_output_directory_path()
        self.output_directory_label.setText(f"默认输出目录：{output_dir}")

    def _refresh_backend_status(self) -> None:
        self.backend_env_label.setText(
            "环境检测："
            f"\nLibreOffice：{self._format_backend_status('libreoffice')}"
            f"\nPandoc：{self._format_backend_status('pandoc')}"
            f"\npdftoppm：{self._format_backend_status('pdftoppm')}"
            f"\npdfinfo：{self._format_backend_status('pdfinfo')}"
            f"\nTesseract：{self._format_backend_status('tesseract')}"
            f"\nFFmpeg：{self._format_backend_status('ffmpeg')}"
            f"\nPyMuPDF：{self._format_backend_status('pymupdf')}"
            f"\npypdf：{self._format_backend_status('pypdf')}"
            f"\npython-docx：{self._format_backend_status('python_docx')}"
            f"\nopenpyxl：{self._format_backend_status('openpyxl')}"
        )

    def _format_backend_status(self, key: str) -> str:
        value = self._backends.get(key, "").strip()
        return value if value else "未检测到"

    def _handle_theme_combo_changed(self, index: int) -> None:
        del index
        theme = self.theme_combo.currentData()
        if theme not in SUPPORTED_THEMES:
            return
        setTheme(theme, save=True)
        self._update_status(f"已切换应用主题：{THEME_LABELS[theme]}。")

    def _handle_font_size_combo_changed(self, index: int) -> None:
        del index
        preset = self.font_size_combo.currentData()
        if not isinstance(preset, FontSizePreset):
            return
        set_font_size_preset(preset)
        self._update_status(f"已切换软件字体大小：{FONT_SIZE_LABELS[preset]}。")

    def _choose_output_directory(self) -> None:
        current = str(get_default_output_directory_path())
        directory = QFileDialog.getExistingDirectory(self, "选择默认输出目录", current)
        if not directory:
            return
        output_dir = set_default_output_directory(directory)
        self._update_status(f"默认输出目录已更新：{output_dir}")

    def _open_output_directory(self) -> None:
        output_dir = ensure_default_output_directory()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(output_dir)))
        self._update_status(f"已请求打开默认输出目录：{output_dir}")

    def _refresh_backends(self) -> None:
        self._backends = detect_document_backends()
        self._refresh_backend_status()
        self._update_status("外部依赖状态已刷新。")

    def _handle_theme_changed_finished(self) -> None:
        self._sync_theme_combo()
        self._apply_styles()

    def _handle_output_directory_changed(self, _value: object) -> None:
        self._update_output_directory_text()

    def _handle_font_size_preset_changed(self, _value: object) -> None:
        self._sync_font_size_combo()
        self._apply_styles()

    def _update_status(self, text: str) -> None:
        self.status_label.setText(text)
