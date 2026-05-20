from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidgetItem,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    LineEdit,
    ListWidget,
    MessageBox,
    PrimaryPushButton,
    PushButton,
    SubtitleLabel,
)

from core.app_settings import ensure_default_output_directory, get_default_output_directory_path, qconfig, app_config
from core.document_tasks import (
    DocumentTask,
    format_task_error,
    DocumentTaskRunner,
    detect_document_backends,
    parse_region_payload_blocks,
    resolve_task_kind,
)
from ui.region_picker_dialog import RegionCanvas, RegionPickerDialog, RegionSelection
from utils.image_utils import open_image_file


TASK_ID_ROLE = int(Qt.ItemDataRole.UserRole) + 1
TASK_STATUS_ROLE = int(Qt.ItemDataRole.UserRole) + 2
TASK_DETAIL_ROLE = int(Qt.ItemDataRole.UserRole) + 3
LOG_DETAIL_ROLE = int(Qt.ItemDataRole.UserRole) + 4


@dataclass(frozen=True)
class ModuleSpec:
    label: str
    summary: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    engines: tuple[str, ...]
    highlights: tuple[str, ...]
    next_step: str
    runtime_note: str
    drop_hint: str
    suffixes: tuple[str, ...]
    queue_enabled: bool = True


MODULE_SPECS = {
    "document": ModuleSpec(
        label="文档转换",
        summary="统一处理 Word / Excel / PPT / Markdown / HTML，优先对接 LibreOffice Headless、Pandoc 和 openpyxl。",
        inputs=("doc/docx/odt", "xls/xlsx/ods", "ppt/pptx", "md/html/txt"),
        outputs=("pdf", "txt", "md", "html", "docx", "epub", "csv", "图片"),
        engines=("LibreOffice Headless", "Pandoc", "openpyxl"),
        highlights=("docx -> pdf", "md -> docx", "pptx -> 图片", "批量转换"),
        next_step="下一步优先补 PDF 合并拆分、OCR 和更多 Office 格式的稳定性处理。",
        runtime_note="当前可执行：Office -> PDF 依赖 LibreOffice，PPT -> 图片会先转 PDF 再转 PNG，Markdown/HTML/TXT -> DOCX 依赖 Pandoc，表格 -> CSV 依赖 openpyxl。",
        drop_hint="拖入 Office、Markdown、HTML 或 TXT 文件，可批量生成转换任务。",
        suffixes=(".doc", ".docx", ".odt", ".xls", ".xlsx", ".ods", ".ppt", ".pptx", ".md", ".html", ".htm", ".txt"),
    ),
    "pdf": ModuleSpec(
        label="PDF 工具",
        summary="聚合 PDF 转换、拆分、合并、压缩、旋转、加解密和 OCR 识别入口。",
        inputs=("pdf",),
        outputs=("转图片", "拆分", "合并", "OCR识别", "压缩", "旋转", "加密", "解密", "水印处理"),
        engines=("pdftoppm", "PyMuPDF", "pypdf"),
        highlights=("PDF 转图片", "PDF 合并拆分", "PDF 压缩旋转", "PDF 水印处理"),
        next_step="下一步优先补更细粒度的旋转角度和图片型水印处理。",
        runtime_note="当前可执行：PDF -> PNG/JPG、PDF 拆分、按选择合并、PDF -> TXT OCR、PDF 压缩、顺时针旋转 90°、自定义口令加解密、文字水印添加。",
        drop_hint="拖入一个或多个 PDF 文件，准备加入 PDF 工具任务队列。",
        suffixes=(".pdf",),
    ),
    "image": ModuleSpec(
        label="图片工具",
        summary="处理图片转 PDF、格式互转、压缩、缩放和批量图片任务。",
        inputs=("jpg/png/webp/heic", "pdf"),
        outputs=("png", "jpg", "pdf", "压缩", "裁剪", "缩放", "批量处理"),
        engines=("Pillow", "pdftoppm", "OpenCV"),
        highlights=("图片转 PDF", "PDF 转图片", "压缩", "批量缩放"),
        next_step="下一步优先补批量压缩和图片尺寸处理。",
        runtime_note="当前可执行：图片 -> PDF、图片 -> PNG/JPG、PDF -> PNG/JPG。",
        drop_hint="拖入图片或 PDF 文件，可统一生成图片工具任务。",
        suffixes=(".jpg", ".jpeg", ".png", ".webp", ".heic", ".bmp", ".tif", ".tiff", ".pdf"),
    ),
    "ocr": ModuleSpec(
        label="OCR 识别",
        summary="支持图片和 PDF 文本识别，后续扩展表格识别、多语言和批量 OCR。",
        inputs=("图片", "PDF"),
        outputs=("txt", "docx", "xlsx", "可搜索 PDF"),
        engines=("Tesseract OCR",),
        highlights=("图片 OCR", "PDF OCR", "多语言识别", "批量 OCR"),
        next_step="下一步优先补 OCR 表格识别和可配置语言包。",
        runtime_note="当前可执行：图片/PDF -> TXT、图片/PDF -> DOCX、图片/PDF -> 可搜索 PDF。优先读取 PDF 文本层，缺失时回退到 Tesseract。",
        drop_hint="拖入图片或 PDF 文件，生成 OCR 识别任务。",
        suffixes=(".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".pdf"),
    ),
    "watermark": ModuleSpec(
        label="去水印",
        summary="区分 PDF 水印和图片水印两条链路，后续接 OpenCV 修复和 AI Inpainting。",
        inputs=("pdf", "图片"),
        outputs=("文本水印删除", "图片修复", "背景填充"),
        engines=("PyMuPDF", "OpenCV"),
        highlights=("PDF 文本水印", "图片局部修复", "背景填充"),
        next_step="下一步优先补框选交互和更智能的图片型水印检测。",
        runtime_note="当前可执行：按关键词删除 PDF 文本/注释类水印与图片文字水印；图片修复/背景填充支持输入 x,y,w,h 区域参数。",
        drop_hint="拖入 PDF 或图片文件，按文件类型分流到不同去水印后端。",
        suffixes=(".pdf", ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"),
    ),
}


class FileDropCard(CardWidget):
    files_dropped = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("documentDropCard")
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(6)

        self.title_label = SubtitleLabel("拖拽文件到这里")
        self.hint_label = BodyLabel("支持文档、PDF、图片等常见处理文件。")
        self.hint_label.setWordWrap(True)

        layout.addWidget(self.title_label)
        layout.addWidget(self.hint_label)

    def set_hint(self, text: str) -> None:
        self.hint_label.setText(text)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls() and self.isEnabled():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if not self.isEnabled():
            event.ignore()
            return
        paths: list[str] = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                paths.append(url.toLocalFile())
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()
            return
        super().dropEvent(event)


class DocumentWorkbench(QWidget):
    SUPPORTED_SUFFIXES = tuple(sorted({suffix for spec in MODULE_SPECS.values() for suffix in spec.suffixes}))

    def __init__(self) -> None:
        super().__init__()
        self._selected_module_key = "document"
        self._tracked_files: list[str] = []
        self._task_sequence = 0
        self._task_records: dict[int, DocumentTask] = {}
        self._task_items: dict[int, QListWidgetItem] = {}
        self._runner: DocumentTaskRunner | None = None
        self._backends = detect_document_backends()
        self._output_root = get_default_output_directory_path()
        self._base_selection_hint_text = ""

        self._build_ui()
        self._apply_styles()
        self._populate_module_nav()
        self.module_nav.setCurrentRow(0)
        self._refresh_backend_status()
        self._refresh_interaction_state()
        self._append_log("文档工作台已接通首批本地任务：图片转 PDF、图片转 PNG/JPG、PDF 转图片。")
        app_config.defaultOutputDirectory.valueChanged.connect(self._handle_output_directory_changed)
        qconfig.themeChangedFinished.connect(self._apply_styles)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        header_card = CardWidget()
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(20, 20, 20, 20)
        header_layout.setSpacing(8)
        header_layout.addWidget(SubtitleLabel("文档工作台"))

        summary_label = BodyLabel(
            "面向文档转换、PDF 工具、图片任务、OCR 和去水印的统一入口。当前已接入首批本地转换执行器，并保留后续扩展位。"
        )
        summary_label.setWordWrap(True)
        header_layout.addWidget(summary_label)

        self.status_label = BodyLabel("准备就绪。")
        self.status_label.setObjectName("documentStatusLabel")
        self.status_label.setWordWrap(True)
        header_layout.addWidget(self.status_label)
        root.addWidget(header_card)

        body = QHBoxLayout()
        body.setSpacing(20)
        root.addLayout(body, 1)

        nav_card = CardWidget()
        nav_card.setFixedWidth(220)
        nav_card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        nav_layout = QVBoxLayout(nav_card)
        nav_layout.setContentsMargins(16, 16, 16, 16)
        nav_layout.setSpacing(12)
        nav_layout.addWidget(SubtitleLabel("模块导航"))

        self.module_nav = ListWidget()
        self.module_nav.currentRowChanged.connect(self._handle_module_changed)
        nav_layout.addWidget(self.module_nav, 1)
        body.addWidget(nav_card, 2)

        center_container = QWidget()
        center_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        center_column = QVBoxLayout(center_container)
        center_column.setSpacing(20)
        center_column.setContentsMargins(0, 0, 0, 0)
        self.center_scroll_area = self._create_column_scroll_area(center_container, "documentCenterScrollArea")
        body.addWidget(self.center_scroll_area, 5)

        overview_card = CardWidget()
        overview_layout = QVBoxLayout(overview_card)
        overview_layout.setContentsMargins(18, 18, 18, 18)
        overview_layout.setSpacing(8)
        self.module_title_label = SubtitleLabel("")
        self.module_summary_label = BodyLabel("")
        self.module_summary_label.setWordWrap(True)
        self.module_highlights_label = BodyLabel("")
        self.module_highlights_label.setWordWrap(True)
        overview_layout.addWidget(self.module_title_label)
        overview_layout.addWidget(self.module_summary_label)
        overview_layout.addWidget(self.module_highlights_label)
        center_column.addWidget(overview_card)

        operation_card = CardWidget()
        operation_layout = QVBoxLayout(operation_card)
        operation_layout.setContentsMargins(18, 18, 18, 18)
        operation_layout.setSpacing(12)
        operation_layout.addWidget(SubtitleLabel("任务草案"))

        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(10)
        form_grid.setVerticalSpacing(8)
        self.source_type_label = BodyLabel("输入类型")
        self.target_type_label = BodyLabel("目标格式 / 动作")
        self.source_combo = ComboBox()
        self.target_combo = ComboBox()
        self.target_combo.currentTextChanged.connect(self._handle_target_changed)
        form_grid.addWidget(self.source_type_label, 0, 0)
        form_grid.addWidget(self.target_type_label, 0, 1)
        form_grid.addWidget(self.source_combo, 1, 0)
        form_grid.addWidget(self.target_combo, 1, 1)
        operation_layout.addLayout(form_grid)

        self.password_label = BodyLabel("PDF 密码")
        self.password_input = LineEdit()
        self.password_input.setPlaceholderText("PDF 加密或解密时可输入自定义密码，留空则使用默认密码 jianji123")
        self.password_input.setClearButtonEnabled(True)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        operation_layout.addWidget(self.password_label)
        operation_layout.addWidget(self.password_input)

        self.text_payload_label = BodyLabel("文本参数")
        self.text_payload_input = LineEdit()
        self.text_payload_input.setClearButtonEnabled(True)
        operation_layout.addWidget(self.text_payload_label)
        operation_layout.addWidget(self.text_payload_input)
        self.pick_region_button = PushButton("框选区域")
        self.pick_region_button.clicked.connect(self._pick_repair_region)
        operation_layout.addWidget(self.pick_region_button)

        self.inline_region_card = CardWidget()
        inline_region_layout = QVBoxLayout(self.inline_region_card)
        inline_region_layout.setContentsMargins(14, 14, 14, 14)
        inline_region_layout.setSpacing(10)
        inline_region_layout.addWidget(SubtitleLabel("修复区域预览"))
        self.inline_region_hint = BodyLabel("当前未载入图片预览。")
        self.inline_region_hint.setWordWrap(True)
        inline_region_layout.addWidget(self.inline_region_hint)
        self.inline_region_host = QWidget()
        self.inline_region_host_layout = QVBoxLayout(self.inline_region_host)
        self.inline_region_host_layout.setContentsMargins(0, 0, 0, 0)
        self.inline_region_host_layout.setSpacing(0)
        inline_region_layout.addWidget(self.inline_region_host)
        inline_region_actions = QHBoxLayout()
        inline_region_actions.setSpacing(8)
        self.inline_region_sync_button = PushButton("同步区域")
        self.inline_region_sync_button.clicked.connect(self._sync_inline_region_payload)
        self.inline_region_clear_button = PushButton("清空区域")
        self.inline_region_clear_button.clicked.connect(self._clear_inline_region_payload)
        self.inline_region_popup_button = PushButton("弹出大图")
        self.inline_region_popup_button.clicked.connect(self._pick_repair_region)
        inline_region_actions.addWidget(self.inline_region_sync_button)
        inline_region_actions.addWidget(self.inline_region_clear_button)
        inline_region_actions.addWidget(self.inline_region_popup_button)
        inline_region_layout.addLayout(inline_region_actions)
        operation_layout.addWidget(self.inline_region_card)
        self.inline_region_canvas: RegionCanvas | None = None
        self._inline_region_source_path: str | None = None

        self.selection_hint_label = BodyLabel("")
        self.selection_hint_label.setWordWrap(True)
        operation_layout.addWidget(self.selection_hint_label)

        action_grid = QGridLayout()
        action_grid.setHorizontalSpacing(10)
        action_grid.setVerticalSpacing(8)
        self.add_files_button = PushButton("添加文件")
        self.add_files_button.clicked.connect(self._pick_files)
        self.add_folder_button = PushButton("导入目录")
        self.add_folder_button.clicked.connect(self._pick_directory)
        self.queue_task_button = PrimaryPushButton("加入任务队列")
        self.queue_task_button.clicked.connect(self._queue_tasks)
        self.clear_files_button = PushButton("清空文件")
        self.clear_files_button.clicked.connect(self._clear_files)
        action_grid.addWidget(self.add_files_button, 0, 0)
        action_grid.addWidget(self.add_folder_button, 0, 1)
        action_grid.addWidget(self.queue_task_button, 1, 0)
        action_grid.addWidget(self.clear_files_button, 1, 1)
        operation_layout.addLayout(action_grid)
        center_column.addWidget(operation_card)

        file_card = CardWidget()
        file_layout = QVBoxLayout(file_card)
        file_layout.setContentsMargins(18, 18, 18, 18)
        file_layout.setSpacing(12)
        file_layout.addWidget(SubtitleLabel("待处理文件"))

        self.drop_card = FileDropCard()
        self.drop_card.files_dropped.connect(self._ingest_paths)
        file_layout.addWidget(self.drop_card)

        self.file_list = ListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.file_list.itemSelectionChanged.connect(self._refresh_file_summary)
        self.file_list.itemSelectionChanged.connect(self._refresh_inline_region_preview)
        file_layout.addWidget(self.file_list, 1)

        file_actions = QHBoxLayout()
        file_actions.setSpacing(10)
        self.remove_selected_files_button = PushButton("删除选中")
        self.remove_selected_files_button.clicked.connect(self._remove_selected_files)
        self.remove_selected_files_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.clear_all_files_button = PushButton("清空全部")
        self.clear_all_files_button.clicked.connect(self._clear_files)
        self.clear_all_files_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        file_actions.addWidget(self.remove_selected_files_button)
        file_actions.addWidget(self.clear_all_files_button)
        file_layout.addLayout(file_actions)

        self.file_summary_label = BodyLabel("当前没有待处理文件。")
        self.file_summary_label.setWordWrap(True)
        file_layout.addWidget(self.file_summary_label)
        center_column.addWidget(file_card, 1)

        right_container = QWidget()
        right_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        right_column = QVBoxLayout(right_container)
        right_column.setSpacing(20)
        right_column.setContentsMargins(0, 0, 0, 0)
        self.right_scroll_area = self._create_column_scroll_area(right_container, "documentRightScrollArea")
        body.addWidget(self.right_scroll_area, 4)

        task_card = CardWidget()
        task_layout = QVBoxLayout(task_card)
        task_layout.setContentsMargins(18, 18, 18, 18)
        task_layout.setSpacing(12)
        task_layout.addWidget(SubtitleLabel("任务队列"))

        self.task_list = ListWidget()
        self.task_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.task_list.itemSelectionChanged.connect(self._refresh_task_summary)
        task_layout.addWidget(self.task_list, 1)

        task_action_grid = QGridLayout()
        task_action_grid.setHorizontalSpacing(10)
        task_action_grid.setVerticalSpacing(8)
        self.start_selected_button = PushButton("执行选中")
        self.start_selected_button.clicked.connect(lambda: self._start_tasks(selected_only=True))
        self.start_all_button = PrimaryPushButton("执行全部")
        self.start_all_button.clicked.connect(lambda: self._start_tasks(selected_only=False))
        self.remove_selected_tasks_button = PushButton("删除选中")
        self.remove_selected_tasks_button.clicked.connect(self._remove_selected_tasks)
        self.clear_tasks_button = PushButton("清空队列")
        self.clear_tasks_button.clicked.connect(self._clear_tasks)
        task_action_grid.addWidget(self.start_selected_button, 0, 0)
        task_action_grid.addWidget(self.start_all_button, 0, 1)
        task_action_grid.addWidget(self.remove_selected_tasks_button, 1, 0)
        task_action_grid.addWidget(self.clear_tasks_button, 1, 1)
        task_layout.addLayout(task_action_grid)

        self.task_summary_label = BodyLabel("当前任务队列为空。")
        self.task_summary_label.setWordWrap(True)
        task_layout.addWidget(self.task_summary_label)
        right_column.addWidget(task_card, 1)

        backend_card = CardWidget()
        backend_layout = QVBoxLayout(backend_card)
        backend_layout.setContentsMargins(18, 18, 18, 18)
        backend_layout.setSpacing(8)
        backend_layout.addWidget(SubtitleLabel("后端路线"))

        self.backend_engines_label = BodyLabel("")
        self.backend_engines_label.setWordWrap(True)
        self.backend_runtime_label = BodyLabel("")
        self.backend_runtime_label.setWordWrap(True)
        self.backend_next_step_label = BodyLabel("")
        self.backend_next_step_label.setWordWrap(True)
        self.backend_env_label = BodyLabel("")
        self.backend_env_label.setWordWrap(True)
        self.output_root_label = BodyLabel("")
        self.output_root_label.setWordWrap(True)
        self.phase_label = BodyLabel("当前已接入：图片转 PDF、图片转 PNG/JPG、PDF 转图片、PDF 合并拆分压缩旋转加解密与文字水印、OCR -> TXT/DOCX/可搜索PDF、图片区域去水印。")
        self.phase_label.setWordWrap(True)

        backend_layout.addWidget(self.backend_engines_label)
        backend_layout.addWidget(self.backend_runtime_label)
        backend_layout.addWidget(self.backend_next_step_label)
        backend_layout.addWidget(self.backend_env_label)
        backend_layout.addWidget(self.output_root_label)
        backend_layout.addWidget(self.phase_label)

        backend_actions = QHBoxLayout()
        backend_actions.setSpacing(10)
        self.refresh_backend_button = PushButton("刷新环境")
        self.refresh_backend_button.clicked.connect(self._handle_refresh_backends)
        self.open_output_button = PushButton("打开输出目录")
        self.open_output_button.clicked.connect(self._open_output_directory)
        backend_actions.addWidget(self.refresh_backend_button)
        backend_actions.addWidget(self.open_output_button)
        backend_layout.addLayout(backend_actions)
        right_column.addWidget(backend_card)

        log_card = CardWidget()
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(18, 18, 18, 18)
        log_layout.setSpacing(12)
        log_layout.addWidget(SubtitleLabel("运行日志"))
        self.log_view = ListWidget()
        self.log_view.itemClicked.connect(self._show_log_detail)
        log_layout.addWidget(self.log_view, 1)
        self.clear_log_button = PushButton("清空日志")
        self.clear_log_button.clicked.connect(self.log_view.clear)
        log_layout.addWidget(self.clear_log_button)
        right_column.addWidget(log_card, 1)

    def _create_column_scroll_area(self, content: QWidget, object_name: str) -> QScrollArea:
        area = QScrollArea()
        area.setObjectName(object_name)
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        area.setWidget(content)
        area.verticalScrollBar().setSingleStep(20)
        area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return area

    def _apply_styles(self) -> None:
        self.status_label.setStyleSheet(
            "background-color: #eef8f3; color: #184c34; border: 1px solid #b9dec9; "
            "border-radius: 10px; padding: 10px 12px;"
        )
        self.drop_card.setStyleSheet(
            """
            QFrame#documentDropCard {
                background-color: #f8fbff;
                border: 1px dashed #8ea8c7;
                border-radius: 14px;
            }
            """
        )
        hint_style = (
            "background-color: #fff7e8; color: #5e3b00; border: 1px solid #f0d6a6; "
            "border-radius: 10px; padding: 8px 10px;"
        )
        for label in [
            self.selection_hint_label,
            self.backend_engines_label,
            self.backend_runtime_label,
            self.backend_next_step_label,
            self.backend_env_label,
            self.output_root_label,
            self.phase_label,
        ]:
            label.setStyleSheet(hint_style)
        scroll_style = (
            """
            QScrollArea#documentCenterScrollArea,
            QScrollArea#documentRightScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea#documentCenterScrollArea > QWidget > QWidget,
            QScrollArea#documentRightScrollArea > QWidget > QWidget {
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
        self.center_scroll_area.setStyleSheet(scroll_style)
        self.right_scroll_area.setStyleSheet(scroll_style)
        for button in self.findChildren(PushButton):
            button.setMinimumHeight(36)
        for button in self.findChildren(PrimaryPushButton):
            button.setMinimumHeight(38)

    def _populate_module_nav(self) -> None:
        for key in ["document", "pdf", "image", "ocr", "watermark"]:
            item = QListWidgetItem(MODULE_SPECS[key].label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.module_nav.addItem(item)

    def _handle_module_changed(self, row: int) -> None:
        if row < 0:
            return
        item = self.module_nav.item(row)
        if item is None:
            return
        module_key = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(module_key, str):
            return
        self._apply_module_spec(module_key)
        self._update_status(f"已切换到 {MODULE_SPECS[module_key].label}。")

    def _apply_module_spec(self, module_key: str) -> None:
        spec = MODULE_SPECS[module_key]
        self._selected_module_key = module_key
        self.module_title_label.setText(spec.label)
        self.module_summary_label.setText(spec.summary)
        self.module_highlights_label.setText(f"本阶段聚焦：{', '.join(spec.highlights)}")
        self.backend_engines_label.setText(f"推荐后端：{', '.join(spec.engines)}")
        self.backend_runtime_label.setText(f"当前可执行范围：{spec.runtime_note}")
        self.backend_next_step_label.setText(f"开发下一步：{spec.next_step}")
        self.selection_hint_label.setText(
            f"当前模块支持：{', '.join(spec.inputs) if spec.inputs else '无需输入选择'}\n"
            f"候选输出：{', '.join(spec.outputs) if spec.outputs else '当前仅预留配置入口'}"
        )
        self._base_selection_hint_text = self.selection_hint_label.text()
        self.drop_card.set_hint(spec.drop_hint)

        self.source_combo.clear()
        self.target_combo.clear()
        if spec.inputs:
            self.source_combo.addItems(list(spec.inputs))
            self.source_combo.setEnabled(True)
        else:
            self.source_combo.addItem("无需选择")
            self.source_combo.setEnabled(False)

        if spec.outputs:
            self.target_combo.addItems(list(spec.outputs))
            self.target_combo.setEnabled(True)
        else:
            self.target_combo.addItem("当前仅配置项")
            self.target_combo.setEnabled(False)

        self._handle_target_changed(self.target_combo.currentText())
        self._refresh_backend_status()
        self._refresh_interaction_state()

    def _handle_target_changed(self, text: str) -> None:
        uses_password = self._selected_module_key == "pdf" and text in {"加密", "解密"}
        self.password_label.setVisible(uses_password)
        self.password_input.setVisible(uses_password)
        uses_text_payload = (
            (self._selected_module_key == "pdf" and text == "水印处理")
            or (self._selected_module_key == "watermark" and text == "文本水印删除")
            or (self._selected_module_key == "watermark" and text in {"图片修复", "背景填充"})
        )
        self.text_payload_label.setVisible(uses_text_payload)
        self.text_payload_input.setVisible(uses_text_payload)
        uses_region_picker = self._selected_module_key == "watermark" and text in {"图片修复", "背景填充"}
        self.pick_region_button.setVisible(uses_region_picker)
        self.inline_region_card.setVisible(uses_region_picker)
        if self._selected_module_key == "pdf" and text == "水印处理":
            self.text_payload_label.setText("水印文字")
            self.text_payload_input.setPlaceholderText("输入要添加到每页上的文字水印，留空时默认使用 CONFIDENTIAL")
        elif self._selected_module_key == "watermark" and text == "文本水印删除":
            self.text_payload_label.setText("匹配关键词")
            self.text_payload_input.setPlaceholderText("输入需要删除的文字水印关键词，例如 CONFIDENTIAL")
        elif self._selected_module_key == "watermark" and text in {"图片修复", "背景填充"}:
            self.text_payload_label.setText("区域参数")
            self.text_payload_input.setPlaceholderText("输入 x,y,w,h；多组可用 ; 分隔，例如 40,30,120,60;180,40,90,50")
        if uses_password:
            self.selection_hint_label.setText(f"{self._base_selection_hint_text}\n当前动作支持自定义密码；留空时默认使用 jianji123。")
        elif uses_text_payload:
            if self._selected_module_key == "pdf":
                self.selection_hint_label.setText(f"{self._base_selection_hint_text}\n当前动作会为每页添加文字水印。")
            elif text in {"图片修复", "背景填充"}:
                self.selection_hint_label.setText(f"{self._base_selection_hint_text}\n当前动作需要提供 x,y,w,h 区域参数；支持多组区域，以 ; 分隔。")
                self._refresh_inline_region_preview()
            else:
                self.selection_hint_label.setText(f"{self._base_selection_hint_text}\n当前动作会按关键词查找并移除文本/注释类水印。")
        else:
            self.selection_hint_label.setText(self._base_selection_hint_text)

    def _pick_repair_region(self) -> None:
        image_path = self._current_previewable_image_path()
        if image_path is None:
            self._update_status("当前没有可用于框选的图片文件。")
            return
        try:
            image = open_image_file(image_path)
        except Exception as exc:
            self._update_status(f"无法加载框选图片：{exc}")
            return
        dialog = RegionPickerDialog(image, self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        payload = dialog.combined_payload()
        if not payload:
            self._update_status("没有选中区域。")
            return
        self.text_payload_input.setText(payload)
        self._apply_payload_to_inline_canvas(payload)
        self._update_status(f"已回填区域：{payload}")

    def _current_previewable_image_path(self) -> str | None:
        candidates = self._selected_or_all_files()
        if not candidates:
            return None
        return next(
            (path for path in candidates if Path(path).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}),
            None,
        )

    def _refresh_inline_region_preview(self) -> None:
        image_path = self._current_previewable_image_path()
        if image_path is None:
            self.inline_region_hint.setText("当前没有可预览的图片文件，请先添加图片。")
            self._set_inline_region_canvas(None, None)
            return
        if image_path == self._inline_region_source_path and self.inline_region_canvas is not None:
            self._apply_payload_to_inline_canvas(self.text_payload_input.text().strip())
            return
        try:
            image = open_image_file(image_path)
        except Exception as exc:
            self.inline_region_hint.setText(f"无法加载预览图片：{exc}")
            self._set_inline_region_canvas(None, None)
            return
        canvas = RegionCanvas(image, minimum_size=(320, 180))
        canvas.selection_changed.connect(lambda _=None: None)
        self._set_inline_region_canvas(canvas, image_path)
        self.inline_region_hint.setText("可直接在下方拖拽框选，点击“同步区域”回填参数。")
        self._apply_payload_to_inline_canvas(self.text_payload_input.text().strip())

    def _set_inline_region_canvas(self, canvas: RegionCanvas | None, source_path: str | None) -> None:
        while self.inline_region_host_layout.count():
            item = self.inline_region_host_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        self.inline_region_canvas = canvas
        self._inline_region_source_path = source_path
        if canvas is not None:
            self.inline_region_host_layout.addWidget(canvas)

    def _sync_inline_region_payload(self) -> None:
        if self.inline_region_canvas is None:
            self._update_status("当前没有可同步的区域预览。")
            return
        payload = self.inline_region_canvas.combined_payload()
        if not payload:
            self._update_status("当前没有框选区域。")
            return
        self.text_payload_input.setText(payload)
        self._update_status(f"已同步区域：{payload}")

    def _clear_inline_region_payload(self) -> None:
        self.text_payload_input.clear()
        if self.inline_region_canvas is not None:
            self.inline_region_canvas.clear_saved_regions()
        self._update_status("已清空区域参数。")

    def _apply_payload_to_inline_canvas(self, payload: str) -> None:
        if self.inline_region_canvas is None:
            return
        regions = [
            RegionSelection(x=x, y=y, width=w, height=h)
            for x, y, w, h in parse_region_payload_blocks(payload, strict=False)
        ]
        self.inline_region_canvas.set_saved_regions(regions)

    def _handle_refresh_backends(self) -> None:
        self._backends = detect_document_backends()
        self._refresh_backend_status()
        self._append_log("已刷新外部依赖检测结果。")
        self._update_status("外部依赖状态已刷新。")

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
        self.output_root_label.setText(f"输出目录：{self._output_root}")

    def _format_backend_status(self, key: str) -> str:
        value = self._backends.get(key, "").strip()
        return value if value else "未检测到"

    def _pick_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "选择待处理文件", "", self._build_file_filter())
        if paths:
            self._ingest_paths(paths)

    def _pick_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择目录")
        if directory:
            self._ingest_paths([directory])

    def _build_file_filter(self) -> str:
        suffixes = " ".join(f"*{suffix}" for suffix in self.SUPPORTED_SUFFIXES)
        return f"Supported Files ({suffixes});;All Files (*)"

    def _ingest_paths(self, paths: list[str]) -> None:
        added = 0
        skipped = 0
        duplicated = 0
        for path in self._expand_paths(paths):
            normalized = str(path.resolve())
            if normalized in self._tracked_files:
                duplicated += 1
                continue
            if path.suffix.lower() not in self.SUPPORTED_SUFFIXES:
                skipped += 1
                continue
            self._tracked_files.append(normalized)
            item = QListWidgetItem(f"{path.name}  |  {path.suffix.lower() or '无扩展名'}")
            item.setToolTip(normalized)
            self.file_list.addItem(item)
            added += 1

        self._refresh_file_summary()
        self._refresh_interaction_state()
        self._refresh_inline_region_preview()
        if added:
            self._update_status(f"已加入 {added} 个文件，当前文件池 {len(self._tracked_files)} 个。")
            self._append_log(f"文件池新增 {added} 个文件，重复 {duplicated} 个，跳过不支持项 {skipped} 个。")
        else:
            self._update_status("没有新增可处理文件。")
            self._append_log(f"本次未新增文件，重复 {duplicated} 个，跳过不支持项 {skipped} 个。")

    def _expand_paths(self, paths: list[str]) -> list[Path]:
        expanded: list[Path] = []
        for raw in paths:
            path = Path(raw)
            if path.is_dir():
                expanded.extend(sorted(item for item in path.rglob("*") if item.is_file()))
            elif path.is_file():
                expanded.append(path)
        return expanded

    def _remove_selected_files(self) -> None:
        rows = sorted({self.file_list.row(item) for item in self.file_list.selectedItems()}, reverse=True)
        if not rows:
            return
        for row in rows:
            self.file_list.takeItem(row)
            self._tracked_files.pop(row)
        self._refresh_file_summary()
        self._refresh_interaction_state()
        self._refresh_inline_region_preview()
        self._update_status(f"已删除 {len(rows)} 个待处理文件。")
        self._append_log(f"文件池移除 {len(rows)} 个文件。")

    def _clear_files(self) -> None:
        removed = len(self._tracked_files)
        self._tracked_files.clear()
        self.file_list.clear()
        self._refresh_file_summary()
        self._refresh_interaction_state()
        self._refresh_inline_region_preview()
        self._update_status("已清空待处理文件。")
        self._append_log(f"文件池已清空，移除 {removed} 个文件。")

    def _queue_tasks(self) -> None:
        spec = MODULE_SPECS[self._selected_module_key]
        if not spec.queue_enabled:
            self._update_status("当前模块为设置中心，不生成任务。")
            return

        candidates = self._selected_or_all_files()
        if not candidates:
            self._update_status("请先添加文件，再创建任务。")
            return

        action_text = self.target_combo.currentText().strip() or "默认目标"
        if self._selected_module_key == "pdf" and action_text == "合并":
            self._queue_pdf_merge_task(spec, candidates)
            return

        created = 0
        incompatible = 0
        unsupported = 0

        for path in candidates:
            suffix = Path(path).suffix.lower()
            if suffix not in spec.suffixes:
                incompatible += 1
                continue
            task_kind, reason = resolve_task_kind(self._selected_module_key, path, action_text)
            if task_kind is None:
                unsupported += 1
                self._append_log(
                    f"{Path(path).name} 未加入队列：{reason}",
                    detail=f"错误码：TASK-UNSUPPORTED\n文件：{path}\n原因：{reason}",
                )
                continue

            self._task_sequence += 1
            task = DocumentTask(
                task_id=self._task_sequence,
                module_key=self._selected_module_key,
                module_label=spec.label,
                action_text=action_text,
                source_path=path,
                task_kind=task_kind,
                password=self._current_pdf_password(),
                text_payload=self._current_text_payload(),
            )
            self._task_records[task.task_id] = task
            item = QListWidgetItem()
            item.setData(TASK_ID_ROLE, task.task_id)
            self.task_list.addItem(item)
            self._task_items[task.task_id] = item
            self._update_task_item(task.task_id, "waiting", "等待中", "已加入任务队列，等待执行。")
            created += 1

        self._refresh_task_summary()
        self._refresh_interaction_state()

        if created:
            self._update_status(f"已创建 {created} 个 {spec.label} 任务。")
            self._append_log(f"{spec.label} 新建任务 {created} 个，目标动作：{action_text}。")
        else:
            self._update_status("当前选择未生成可执行任务。")

        if incompatible:
            self._append_log(
                f"{spec.label} 跳过 {incompatible} 个与当前模块不匹配的文件。",
                detail=f"错误码：TASK-INCOMPATIBLE\n模块：{spec.label}\n原因：输入文件类型与当前模块不匹配。",
            )
        if unsupported:
            self._append_log(
                f"{spec.label} 跳过 {unsupported} 个当前未接入执行器的任务。",
                detail=f"错误码：TASK-UNSUPPORTED\n模块：{spec.label}\n原因：目标动作在当前文件类型下尚未接入执行器。",
            )

    def _queue_pdf_merge_task(self, spec: ModuleSpec, candidates: list[str]) -> None:
        pdf_paths = [path for path in candidates if Path(path).suffix.lower() == ".pdf"]
        if len(pdf_paths) < 2:
            self._update_status("PDF 合并至少需要 2 个 PDF 文件。")
            self._append_log("PDF 合并未加入队列：待处理 PDF 数量不足 2 个。")
            return

        self._task_sequence += 1
        first_name = Path(pdf_paths[0]).name
        task = DocumentTask(
            task_id=self._task_sequence,
            module_key=self._selected_module_key,
            module_label=spec.label,
            action_text="合并",
            source_path=pdf_paths[0],
            task_kind="pdf_merge",
            related_paths=tuple(pdf_paths),
            password=self._current_pdf_password(),
            text_payload=self._current_text_payload(),
        )
        self._task_records[task.task_id] = task
        item = QListWidgetItem()
        item.setData(TASK_ID_ROLE, task.task_id)
        self.task_list.addItem(item)
        self._task_items[task.task_id] = item
        self._update_task_item(
            task.task_id,
            "waiting",
            "等待中",
            f"已加入 PDF 合并任务，待合并 {len(pdf_paths)} 个文件，首文件：{first_name}。",
        )
        self._refresh_task_summary()
        self._refresh_interaction_state()
        self._update_status(f"已创建 1 个 PDF 合并任务，包含 {len(pdf_paths)} 个文件。")
        self._append_log(f"PDF 合并任务已加入队列，共包含 {len(pdf_paths)} 个文件。")

    def _selected_or_all_files(self) -> list[str]:
        selected_rows = sorted({self.file_list.row(item) for item in self.file_list.selectedItems()})
        if selected_rows:
            return [self._tracked_files[row] for row in selected_rows]
        return list(self._tracked_files)

    def _current_pdf_password(self) -> str:
        if self._selected_module_key == "pdf" and self.target_combo.currentText() in {"加密", "解密"}:
            return self.password_input.text().strip()
        return ""

    def _current_text_payload(self) -> str:
        target = self.target_combo.currentText()
        if self._selected_module_key == "pdf" and target == "水印处理":
            return self.text_payload_input.text().strip()
        if self._selected_module_key == "watermark" and target in {"文本水印删除", "图片修复", "背景填充"}:
            return self.text_payload_input.text().strip()
        return ""

    def _start_tasks(self, selected_only: bool) -> None:
        if self._runner is not None and self._runner.isRunning():
            self._update_status("当前已有任务正在执行。")
            return

        task_ids = self._selected_task_ids(selected_only=selected_only)
        if not task_ids:
            self._update_status("没有可执行的任务。")
            return

        tasks = [self._task_records[task_id] for task_id in task_ids if task_id in self._task_records]
        if not tasks:
            self._update_status("没有找到可执行的任务记录。")
            return

        self._runner = DocumentTaskRunner(tasks, self._output_root)
        self._runner.task_state_changed.connect(self._handle_task_state_changed)
        self._runner.batch_finished.connect(self._handle_batch_finished)
        self._runner.finished.connect(self._cleanup_runner)
        self._runner.start()
        self._refresh_interaction_state()
        scope_text = "选中任务" if selected_only else "任务队列"
        self._update_status(f"开始执行 {scope_text}，共 {len(tasks)} 项。")
        self._append_log(f"开始执行 {len(tasks)} 个任务。")

    def _selected_task_ids(self, selected_only: bool) -> list[int]:
        if selected_only:
            items = self.task_list.selectedItems()
        else:
            items = [self.task_list.item(row) for row in range(self.task_list.count())]
        task_ids: list[int] = []
        for item in items:
            if item is None:
                continue
            task_id = item.data(TASK_ID_ROLE)
            if isinstance(task_id, int):
                task_ids.append(task_id)
        return task_ids

    def _handle_task_state_changed(self, task_id: int, status_key: str, status_label: str, detail: str) -> None:
        self._update_task_item(task_id, status_key, status_label, detail)
        source_name = Path(self._task_records[task_id].source_path).name if task_id in self._task_records else str(task_id)
        log_detail = None
        if status_key == "failed":
            code, message = self._split_error_code(detail)
            log_detail = (
                f"错误码：{code}\n任务：#{task_id:03d}\n文件：{source_name}\n状态：{status_label}\n详细原因：{message}"
            )
        self._append_log(f"任务 #{task_id:03d} {status_label}：{source_name}。{detail}", detail=log_detail)
        if status_key == "running":
            self._update_status(f"正在处理任务 #{task_id:03d}：{source_name}")

    def _handle_batch_finished(self, total: int, success_count: int, failed_count: int) -> None:
        self._refresh_task_summary()
        self._refresh_interaction_state()
        self._update_status(f"任务执行完成：共 {total} 项，成功 {success_count} 项，失败 {failed_count} 项。")
        self._append_log(f"本轮执行完成：共 {total} 项，成功 {success_count} 项，失败 {failed_count} 项。")

    def _cleanup_runner(self) -> None:
        self._runner = None
        self._refresh_interaction_state()

    def _update_task_item(self, task_id: int, status_key: str, status_label: str, detail: str) -> None:
        task = self._task_records.get(task_id)
        item = self._task_items.get(task_id)
        if task is None or item is None:
            return
        item.setText(f"#{task.task_id:03d} [{status_label}] {task.module_label} | {Path(task.source_path).name} -> {task.action_text}")
        item.setToolTip(
            f"任务 #{task.task_id:03d}\n模块：{task.module_label}\n输入：{task.source_path}\n动作：{task.action_text}\n"
            f"执行器：{task.task_kind}\n状态：{status_label}\n详情：{detail}"
        )
        item.setData(TASK_STATUS_ROLE, status_key)
        item.setData(TASK_DETAIL_ROLE, detail)
        item.setForeground(self._task_color(status_key))

    def _task_color(self, status_key: str) -> QColor:
        if status_key == "running":
            return QColor("#185abd")
        if status_key == "success":
            return QColor("#1a7f37")
        if status_key == "failed":
            return QColor("#c52828")
        return QColor("#465364")

    def _remove_selected_tasks(self) -> None:
        rows = sorted({self.task_list.row(item) for item in self.task_list.selectedItems()}, reverse=True)
        if not rows:
            return
        removed_ids: list[int] = []
        for row in rows:
            item = self.task_list.takeItem(row)
            if item is None:
                continue
            task_id = item.data(TASK_ID_ROLE)
            if isinstance(task_id, int):
                removed_ids.append(task_id)
        for task_id in removed_ids:
            self._task_records.pop(task_id, None)
            self._task_items.pop(task_id, None)
        self._refresh_task_summary()
        self._refresh_interaction_state()
        self._update_status(f"已删除 {len(removed_ids)} 个任务。")
        self._append_log(f"任务队列移除 {len(removed_ids)} 个任务。")

    def _clear_tasks(self) -> None:
        removed = self.task_list.count()
        self.task_list.clear()
        self._task_records.clear()
        self._task_items.clear()
        self._refresh_task_summary()
        self._refresh_interaction_state()
        self._update_status("已清空任务队列。")
        self._append_log(f"任务队列已清空，移除 {removed} 个任务。")

    def _refresh_file_summary(self) -> None:
        total = self.file_list.count()
        selected = len(self.file_list.selectedItems())
        if total == 0:
            self.file_summary_label.setText("当前没有待处理文件。支持拖拽文件或导入目录。")
        else:
            self.file_summary_label.setText(
                f"当前文件 {total} 个，已选 {selected} 个。未选中时默认按全部文件生成批量任务。"
            )
        self._refresh_interaction_state()

    def _refresh_task_summary(self) -> None:
        total = self.task_list.count()
        selected = len(self.task_list.selectedItems())
        if total == 0:
            self.task_summary_label.setText("当前任务队列为空。可先加入任务，再执行首批本地转换。")
        else:
            self.task_summary_label.setText(f"当前队列 {total} 个任务，已选 {selected} 个。状态支持等待中、执行中、成功、失败。")
        self._refresh_interaction_state()

    def _refresh_interaction_state(self) -> None:
        running = self._runner is not None and self._runner.isRunning()
        queue_enabled = MODULE_SPECS[self._selected_module_key].queue_enabled
        total_files = self.file_list.count()
        selected_files = len(self.file_list.selectedItems())
        total_tasks = self.task_list.count()
        selected_tasks = len(self.task_list.selectedItems())

        self.add_files_button.setEnabled(queue_enabled and not running)
        self.add_folder_button.setEnabled(queue_enabled and not running)
        self.queue_task_button.setEnabled(queue_enabled and total_files > 0 and not running)
        self.clear_files_button.setEnabled(total_files > 0 and not running)
        self.clear_all_files_button.setEnabled(total_files > 0 and not running)
        self.remove_selected_files_button.setEnabled(selected_files > 0 and not running)
        self.drop_card.setEnabled(queue_enabled and not running)

        self.start_selected_button.setEnabled(selected_tasks > 0 and not running)
        self.start_all_button.setEnabled(total_tasks > 0 and not running)
        self.remove_selected_tasks_button.setEnabled(selected_tasks > 0 and not running)
        self.clear_tasks_button.setEnabled(total_tasks > 0 and not running)

        self.refresh_backend_button.setEnabled(not running)
        self.open_output_button.setEnabled(True)

    def _handle_output_directory_changed(self, _value: object) -> None:
        self._output_root = get_default_output_directory_path()
        self._refresh_backend_status()

    def _open_output_directory(self) -> None:
        self._output_root = ensure_default_output_directory()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._output_root)))
        self._append_log(f"已请求打开输出目录：{self._output_root}")

    def _show_log_detail(self, item: QListWidgetItem) -> None:
        detail = item.data(LOG_DETAIL_ROLE)
        if not isinstance(detail, str) or not detail.strip():
            return
        MessageBox("日志详情", detail, self).exec()

    def _split_error_code(self, detail: str) -> tuple[str, str]:
        if detail.startswith("[") and "]" in detail:
            code = detail[1 : detail.index("]")]
            message = detail[detail.index("]") + 1 :].strip()
            return code, message
        return "TASK-UNEXPECTED", detail

    def _update_status(self, text: str) -> None:
        self.status_label.setText(text)

    def _append_log(self, message: str, detail: str | None = None) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        item = QListWidgetItem(f"{timestamp}  {message}")
        if detail:
            item.setData(LOG_DETAIL_ROLE, detail)
            item.setToolTip("点击查看详情")
            item.setForeground(QColor("#185abd"))
        self.log_view.addItem(item)
        self.log_view.scrollToBottom()
