from __future__ import annotations

from importlib.util import find_spec
from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QFrame, QLabel, QProgressDialog, QVBoxLayout, QWidget, QSizePolicy
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    CompactDoubleSpinBox,
    PrimaryPushButton,
    PushButton,
    RadioButton,
    SpinBox,
    SwitchButton,
    TextEdit,
)

from ui.export_support import (
    DNN_SUPERRES_MODEL_SPECS,
    SUPERRES_MODEL_CACHE_DIR,
    ExportImageThread,
    ModelDownloadThread,
)
from utils.image_utils import (
    enhance_image_dnn_superres,
    enhance_image_srcnn,
    enhance_image_super_resolution,
    infer_dnn_model_metadata,
    pil_to_qpixmap,
    resolve_export_path,
    scaled_preview_image,
)


class ExportMixin:
    def _build_export_panel(self) -> QWidget:
        page = QWidget()
        layout = self._panel_layout(page, "高清导出与增强")

        self.export_quality_spin = SpinBox()
        self.export_quality_spin.setRange(1, 100)
        self.export_quality_spin.setValue(95)
        self.export_enhance_switch = SwitchButton()
        self.export_enhance_switch.setChecked(False)
        self.export_sr_radio = RadioButton("超分辨率重建技术")
        self.export_srcnn_radio = RadioButton("PyTorch SRCNN")
        self.export_dnn_radio = RadioButton("OpenCV dnn_superres")
        self.export_sr_radio.setChecked(True)
        self.export_hd_scale_spin = CompactDoubleSpinBox()
        self.export_hd_scale_spin.setRange(1.0, 4.0)
        self.export_hd_scale_spin.setSingleStep(0.25)
        self.export_hd_scale_spin.setValue(2.0)
        self.export_hd_sharpen_spin = CompactDoubleSpinBox()
        self.export_hd_sharpen_spin.setRange(1.0, 3.0)
        self.export_hd_sharpen_spin.setSingleStep(0.1)
        self.export_hd_sharpen_spin.setValue(1.25)
        self.export_srcnn_model_path = TextEdit()
        self.export_srcnn_model_path.setFixedHeight(42)
        self.export_srcnn_model_path.setPlaceholderText("SRCNN 模型路径，例如 /path/to/srcnn_x2.pth")
        self.export_srcnn_browse_button = PushButton("选择 SRCNN 模型")
        self.export_srcnn_browse_button.clicked.connect(self.pick_srcnn_model_file)
        self.export_dnn_model_combo = ComboBox()
        for key, spec in DNN_SUPERRES_MODEL_SPECS.items():
            self.export_dnn_model_combo.addItem(spec["label"], userData=key)
        self.export_dnn_model_combo.currentIndexChanged.connect(self._on_export_dnn_model_changed)
        self.export_dnn_scale_spin = SpinBox()
        self.export_dnn_scale_combo = ComboBox()
        self.export_dnn_scale_combo.currentIndexChanged.connect(self._on_export_dnn_scale_changed)
        self.export_dnn_model_path = TextEdit()
        self.export_dnn_model_path.setFixedHeight(42)
        self.export_dnn_model_path.setPlaceholderText("dnn_superres 模型路径，例如 /path/to/EDSR_x4.pb")
        self.export_dnn_browse_button = PushButton("选择 dnn_superres 模型")
        self.export_dnn_browse_button.clicked.connect(self.pick_dnn_model_file)
        self.export_dnn_download_button = PushButton("训练资料")
        self.export_dnn_download_button.clicked.connect(self.open_selected_dnn_download_docs)
        self.export_dnn_fetch_button = PrimaryPushButton("下载模型")
        self.export_dnn_fetch_button.clicked.connect(self.download_selected_dnn_model)
        self.export_dnn_code_button = PushButton("实现代码")
        self.export_dnn_code_button.clicked.connect(self.open_selected_dnn_code_docs)
        self.export_dnn_paper_button = PushButton("论文")
        self.export_dnn_paper_button.clicked.connect(self.open_selected_dnn_paper_docs)
        self.export_dnn_info_label = BodyLabel("")
        self.export_dnn_info_label.setObjectName("panelHintLabel")
        self.export_dnn_info_label.setWordWrap(True)

        layout.addWidget(BodyLabel("导出质量"))
        layout.addWidget(self.export_quality_spin)
        layout.addWidget(BodyLabel("高清增强"))
        layout.addWidget(self.export_enhance_switch)
        layout.addWidget(BodyLabel("增强方式"))
        layout.addWidget(self.export_sr_radio)
        layout.addWidget(self.export_srcnn_radio)
        layout.addWidget(self.export_dnn_radio)
        layout.addWidget(BodyLabel("放大倍率"))
        layout.addWidget(self.export_hd_scale_spin)
        layout.addWidget(BodyLabel("锐化强度 / 经典超分"))
        layout.addWidget(self.export_hd_sharpen_spin)
        layout.addWidget(BodyLabel("SRCNN 模型路径"))
        layout.addWidget(self.export_srcnn_model_path)
        layout.addWidget(self.export_srcnn_browse_button)
        layout.addWidget(BodyLabel("OpenCV dnn_superres 模型"))
        layout.addWidget(self.export_dnn_model_combo)
        layout.addWidget(BodyLabel("训练模型倍率"))
        layout.addWidget(self.export_dnn_scale_combo)
        layout.addWidget(BodyLabel("dnn_superres 模型路径"))
        layout.addWidget(self.export_dnn_model_path)
        layout.addWidget(self.export_dnn_browse_button)
        doc_actions = QVBoxLayout()
        doc_actions.setSpacing(8)
        for button in [
            self.export_dnn_fetch_button,
            self.export_dnn_download_button,
            self.export_dnn_code_button,
            self.export_dnn_paper_button,
        ]:
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            doc_actions.addWidget(button)
        layout.addLayout(doc_actions)
        layout.addWidget(self.export_dnn_info_label)

        layout.addWidget(BodyLabel("导出前预览"))
        self.export_before_preview = self._create_export_preview_card()
        layout.addWidget(self.export_before_preview)
        layout.addWidget(BodyLabel("增强后预览"))
        self.export_after_preview = self._create_export_preview_card()
        layout.addWidget(self.export_after_preview)
        preview_btn = PushButton("刷新高清预览")
        preview_btn.clicked.connect(self.update_export_comparison_preview)
        export_btn = PrimaryPushButton("导出当前图片")
        export_btn.clicked.connect(self.export_image_dialog)
        preview_actions = QVBoxLayout()
        preview_actions.setSpacing(8)
        preview_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        export_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        preview_actions.addWidget(preview_btn)
        preview_actions.addWidget(export_btn)
        layout.addLayout(preview_actions)

        self.export_hint_label = BodyLabel("支持经典超分、SRCNN 与 4 种 OpenCV dnn_superres 模型，可选在线资料或本地自定义模型。")
        self.export_hint_label.setObjectName("panelHintLabel")
        self.export_hint_label.setWordWrap(True)
        layout.addWidget(self.export_hint_label)
        layout.addStretch(1)
        self._sync_export_dnn_model_controls()
        self._sync_optional_export_backends()
        return page

    def export_image_dialog(self) -> None:
        if self.image_model.current_image is None:
            self._show_error("请先导入图片。")
            return
        if self._export_thread is not None and self._export_thread.isRunning():
            self._show_error("当前已有导出任务正在进行，请先等待完成或取消。")
            return
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "导出图片",
            "",
            "PNG (*.png);;JPEG (*.jpg *.jpeg)",
        )
        if not path:
            return
        path = resolve_export_path(path, selected_filter)
        try:
            export_image = self._build_export_image()
        except Exception as exc:
            self._show_error(f"导出失败：{exc}")
            return
        self._start_export_task(export_image, path, self.export_quality_spin.value())

    def update_export_comparison_preview(self) -> None:
        image = self.image_model.current_image
        if image is None:
            return
        before = self.text_controller.render(image, self.image_model.text_items)
        before_thumb, _ = scaled_preview_image(before, 200)
        cache_key = self._build_export_preview_cache_key(before)
        try:
            if not self.export_enhance_switch.isChecked():
                after_thumb = before_thumb.copy()
            elif self._export_preview_cache_key == cache_key and self._export_preview_cache_image is not None:
                after_thumb = self._export_preview_cache_image.copy()
            else:
                after_thumb = self._apply_selected_export_enhancer(before_thumb)
                self._export_preview_cache_key = cache_key
                self._export_preview_cache_image = after_thumb.copy()
            self.export_hint_label.setText("预览已更新，可对比导出前后效果。")
        except Exception as exc:
            after_thumb = before_thumb.copy()
            self._invalidate_export_preview_cache()
            self.export_hint_label.setText(f"增强预览失败：{exc}")
        self._set_export_preview_image(self.export_before_preview, before_thumb)
        self._set_export_preview_image(self.export_after_preview, after_thumb)

    def _create_export_preview_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("exportPreviewFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setMinimumSize(160, 160)
        label.setMaximumSize(180, 180)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(label, 0, Qt.AlignmentFlag.AlignCenter)
        frame._preview_label = label  # type: ignore[attr-defined]
        return frame

    def _set_export_preview_image(self, frame: QWidget, image: Image.Image) -> None:
        label = frame._preview_label  # type: ignore[attr-defined]
        label.setPixmap(pil_to_qpixmap(image))

    def _build_export_preview_cache_key(self, image: Image.Image) -> tuple:
        return (
            id(image),
            image.size,
            self.export_enhance_switch.isChecked(),
            self.export_sr_radio.isChecked(),
            self.export_srcnn_radio.isChecked(),
            self.export_dnn_radio.isChecked(),
            round(self.export_hd_scale_spin.value(), 2),
            round(self.export_hd_sharpen_spin.value(), 2),
            self.export_srcnn_model_path.toPlainText().strip(),
            self._current_dnn_model_key(),
            self._current_dnn_scale(),
            self.export_dnn_model_path.toPlainText().strip(),
            len(self.image_model.text_items),
        )

    def _invalidate_export_preview_cache(self) -> None:
        self._export_preview_cache_key = None
        self._export_preview_cache_image = None

    def pick_srcnn_model_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择 SRCNN 模型文件", "", "PyTorch Models (*.pth *.pt);;All Files (*)")
        if path:
            self.export_srcnn_model_path.setPlainText(path)
            self._invalidate_export_preview_cache()

    def pick_dnn_model_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择 dnn_superres 模型文件", "", "TensorFlow Models (*.pb);;All Files (*)")
        if not path:
            return
        self.export_dnn_model_path.setPlainText(path)
        self._apply_dnn_model_guess_from_path(path)
        self._invalidate_export_preview_cache()

    def _apply_dnn_model_guess_from_path(self, path: str) -> None:
        guessed_model, guessed_scale = infer_dnn_model_metadata(path)
        if guessed_model is not None:
            index = self.export_dnn_model_combo.findData(guessed_model)
            if index >= 0:
                self.export_dnn_model_combo.setCurrentIndex(index)
        if guessed_scale is not None:
            scale_index = self.export_dnn_scale_combo.findData(guessed_scale)
            if scale_index >= 0:
                self.export_dnn_scale_combo.setCurrentIndex(scale_index)
        details = []
        if guessed_model is not None:
            details.append(f"模型 {guessed_model}")
        if guessed_scale is not None:
            details.append(f"倍率 x{guessed_scale}")
        if details:
            self._update_status(f"已识别模型文件 {Path(path).name}：" + "，".join(details))

    def _current_dnn_model_key(self) -> str:
        key = self.export_dnn_model_combo.currentData()
        if isinstance(key, str) and key in DNN_SUPERRES_MODEL_SPECS:
            return key
        return "edsr"

    def _current_dnn_spec(self) -> dict:
        return DNN_SUPERRES_MODEL_SPECS[self._current_dnn_model_key()]

    def _current_dnn_scale(self) -> int:
        scale = self.export_dnn_scale_combo.currentData()
        if isinstance(scale, int):
            return scale
        return int(self.export_dnn_scale_spin.value())

    def _build_dnn_model_filename(self, model_key: str, scale: int) -> str:
        spec = DNN_SUPERRES_MODEL_SPECS[model_key]
        return f"{spec['label']}_x{scale}.pb"

    def _build_dnn_model_download_url(self, model_key: str, scale: int) -> str:
        spec = DNN_SUPERRES_MODEL_SPECS[model_key]
        return f"{spec['download_raw_base']}/{self._build_dnn_model_filename(model_key, scale)}"

    def _build_dnn_model_cache_path(self, model_key: str, scale: int) -> Path:
        return SUPERRES_MODEL_CACHE_DIR / self._build_dnn_model_filename(model_key, scale)

    def _is_managed_dnn_cache_path(self, path: str) -> bool:
        if not path:
            return False
        try:
            return Path(path).resolve().parent == SUPERRES_MODEL_CACHE_DIR.resolve()
        except Exception:
            return False

    def _sync_optional_export_backends(self) -> None:
        srcnn_available = find_spec("torch") is not None
        self.export_srcnn_radio.setEnabled(srcnn_available)
        self.export_srcnn_model_path.setEnabled(srcnn_available)
        self.export_srcnn_browse_button.setEnabled(srcnn_available)
        if srcnn_available:
            self.export_srcnn_radio.setText("PyTorch SRCNN")
            self.export_srcnn_model_path.setPlaceholderText("SRCNN 模型路径，例如 /path/to/srcnn_x2.pth")
            return

        self.export_srcnn_radio.setText("PyTorch SRCNN（需 torch）")
        self.export_srcnn_radio.setChecked(False)
        self.export_sr_radio.setChecked(True)
        self.export_srcnn_model_path.setPlainText("")
        self.export_srcnn_model_path.setPlaceholderText("当前构建未包含 torch，SRCNN 已禁用。")

    def _sync_export_dnn_model_controls(self) -> None:
        spec = self._current_dnn_spec()
        current_scale = self.export_dnn_scale_combo.currentData()
        self.export_dnn_scale_combo.blockSignals(True)
        self.export_dnn_scale_combo.clear()
        for scale in spec["scales"]:
            self.export_dnn_scale_combo.addItem(f"x{scale}", userData=scale)
        target_scale = current_scale if current_scale in spec["scales"] else spec["scales"][-1]
        scale_index = self.export_dnn_scale_combo.findData(target_scale)
        if scale_index >= 0:
            self.export_dnn_scale_combo.setCurrentIndex(scale_index)
        self.export_dnn_scale_combo.blockSignals(False)
        self.export_dnn_scale_spin.setRange(min(spec["scales"]), max(spec["scales"]))
        self.export_dnn_scale_spin.setValue(int(target_scale))
        self.export_dnn_model_path.setPlaceholderText(
            f"dnn_superres 模型路径，例如 /path/to/{spec['label']}_x{target_scale}.pb"
        )
        cache_path = self._build_dnn_model_cache_path(self._current_dnn_model_key(), int(target_scale))
        current_path = self.export_dnn_model_path.toPlainText().strip()
        if cache_path.exists():
            if not current_path or self._is_managed_dnn_cache_path(current_path):
                self.export_dnn_model_path.setPlainText(str(cache_path))
        elif not current_path or self._is_managed_dnn_cache_path(current_path):
            self.export_dnn_model_path.setPlainText("")
        self.export_dnn_info_label.setText(
            f"{spec['label']}：{spec['summary']} {spec['details']} 可直接下载到本地缓存 {cache_path}，也可手动指定本地 .pb 文件。"
        )

    def _on_export_dnn_model_changed(self, index: int) -> None:
        del index
        self._sync_export_dnn_model_controls()
        self.update_export_comparison_preview()

    def _on_export_dnn_scale_changed(self, index: int) -> None:
        del index
        scale = self.export_dnn_scale_combo.currentData()
        if isinstance(scale, int):
            self.export_dnn_scale_spin.setValue(scale)
        self.update_export_comparison_preview()

    def _open_url(self, url: str) -> None:
        qurl = QUrl(url)
        if QDesktopServices.openUrl(qurl):
            return
        self._show_error(f"无法打开链接：{qurl.toString()}")

    def open_selected_dnn_download_docs(self) -> None:
        self._open_url(self._current_dnn_spec()["download_url"])

    def open_selected_dnn_code_docs(self) -> None:
        self._open_url(self._current_dnn_spec()["code_url"])

    def open_selected_dnn_paper_docs(self) -> None:
        self._open_url(self._current_dnn_spec()["paper_url"])

    def download_selected_dnn_model(self) -> None:
        if self._model_download_thread is not None and self._model_download_thread.isRunning():
            self._show_error("当前已有模型正在下载，请稍候。")
            return
        model_key = self._current_dnn_model_key()
        scale = self._current_dnn_scale()
        target_path = self._build_dnn_model_cache_path(model_key, scale)
        if target_path.exists():
            self.export_dnn_model_path.setPlainText(str(target_path))
            self._apply_dnn_model_guess_from_path(str(target_path))
            self._update_status(f"已复用本地模型：{target_path.name}")
            return
        url = self._build_dnn_model_download_url(model_key, scale)
        self.export_dnn_fetch_button.setEnabled(False)
        self.export_dnn_fetch_button.setText("下载中...")
        self._update_status(f"开始下载模型：{target_path.name}")
        self._model_download_thread = ModelDownloadThread(url, target_path, self)
        self._model_download_thread.progress_changed.connect(self._update_status)
        self._model_download_thread.download_finished.connect(self._handle_dnn_model_download_finished)
        self._model_download_thread.download_failed.connect(self._handle_dnn_model_download_failed)
        self._model_download_thread.finished.connect(self._reset_dnn_download_button_state)
        self._model_download_thread.start()

    def _handle_dnn_model_download_finished(self, path: str) -> None:
        self.export_dnn_model_path.setPlainText(path)
        self._apply_dnn_model_guess_from_path(path)
        self._update_status(f"模型下载完成：{Path(path).name}")

    def _handle_dnn_model_download_failed(self, message: str) -> None:
        self._show_error(message)
        self._update_status(message)

    def _reset_dnn_download_button_state(self) -> None:
        self.export_dnn_fetch_button.setEnabled(True)
        self.export_dnn_fetch_button.setText("下载模型到本地")
        self._model_download_thread = None

    def _build_export_image(self) -> Image.Image:
        image = self.image_model.current_image
        if image is None:
            raise ValueError("请先导入图片。")
        export_image = self.text_controller.render(image, self.image_model.text_items)
        if self.export_enhance_switch.isChecked():
            export_image = self._apply_selected_export_enhancer(export_image)
        return export_image

    def _apply_selected_export_enhancer(self, image: Image.Image) -> Image.Image:
        if self.export_sr_radio.isChecked():
            return enhance_image_super_resolution(
                image,
                scale_factor=self.export_hd_scale_spin.value(),
                sharpen_strength=self.export_hd_sharpen_spin.value(),
            )
        if self.export_srcnn_radio.isChecked():
            return enhance_image_srcnn(
                image,
                scale_factor=self.export_hd_scale_spin.value(),
                model_path=self.export_srcnn_model_path.toPlainText().strip(),
            )
        if self.export_dnn_radio.isChecked():
            return enhance_image_dnn_superres(
                image,
                model_name=self._current_dnn_model_key(),
                scale=int(self.export_dnn_scale_combo.currentData() or self.export_dnn_scale_spin.value()),
                model_path=self.export_dnn_model_path.toPlainText().strip(),
            )
        return image

    def _start_export_task(self, image: Image.Image, path: str, quality: int) -> None:
        dialog = QProgressDialog("正在准备导出…", "取消导出", 0, 100, self)
        dialog.setWindowTitle("导出进度")
        dialog.setAutoClose(False)
        dialog.setAutoReset(False)
        dialog.setMinimumDuration(0)
        dialog.setValue(0)
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.canceled.connect(self._cancel_export_task)
        self._export_progress_dialog = dialog
        self._export_thread = ExportImageThread(image, path, quality, self)
        self._export_thread.progress_changed.connect(self._handle_export_progress)
        self._export_thread.export_finished.connect(self._handle_export_finished)
        self._export_thread.export_failed.connect(self._handle_export_failed)
        self._export_thread.export_cancelled.connect(self._handle_export_cancelled)
        self._export_thread.finished.connect(self._cleanup_export_task)
        self._export_thread.start()
        dialog.show()
        self._update_status("导出任务已开始。")

    def _handle_export_progress(self, percent: int, stage: str, eta: str) -> None:
        if self._export_progress_dialog is None:
            return
        self._export_progress_dialog.setLabelText(f"{stage}\n{eta}")
        self._export_progress_dialog.setValue(percent)
        self._update_status(f"{stage} {percent}%  {eta}")

    def _handle_export_finished(self, path: str) -> None:
        if self._export_progress_dialog is not None:
            self._export_progress_dialog.setValue(100)
            self._export_progress_dialog.setLabelText("导出完成\n预计剩余时间：0 秒")
            self._export_progress_dialog.setCancelButton(None)
            self._export_progress_dialog.close()
        self._update_status(f"已导出到：{path}")

    def _handle_export_failed(self, message: str) -> None:
        if self._export_progress_dialog is not None:
            self._export_progress_dialog.close()
        self._show_error(f"导出失败：{message}")
        self._update_status(f"导出失败：{message}")

    def _handle_export_cancelled(self, message: str) -> None:
        if self._export_progress_dialog is not None:
            self._export_progress_dialog.setCancelButton(None)
            self._export_progress_dialog.close()
        self._update_status(message)

    def _cancel_export_task(self) -> None:
        if self._export_thread is not None:
            self._export_thread.cancel()
            self._update_status("正在取消导出任务…")

    def _cleanup_export_task(self) -> None:
        if self._export_progress_dialog is not None:
            self._export_progress_dialog.deleteLater()
            self._export_progress_dialog = None
        if self._export_thread is not None:
            self._export_thread.deleteLater()
            self._export_thread = None
