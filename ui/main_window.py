from __future__ import annotations

from pathlib import Path
from typing import Optional

from PIL import Image
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QListWidgetItem,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
    QProgressDialog,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ColorPickerButton,
    ComboBox,
    CompactDoubleSpinBox,
    DoubleSpinBox,
    FluentIcon,
    FluentWindow,
    InfoBar,
    InfoBarPosition,
    ListWidget,
    MessageBox,
    NavigationItemPosition,
    PrimaryPushButton,
    PushButton,
    RadioButton,
    SegmentedWidget,
    Slider,
    SpinBox,
    StrongBodyLabel,
    SubtitleLabel,
    SwitchButton,
    TextEdit,
    ToolButton,
)

from core.crop_controller import CropController
from core.history_manager import HistoryManager
from core.image_model import ImageModel
from core.mesh_warp_controller import MeshWarpController
from core.perspective_controller import PerspectiveController
from core.text_controller import TextOverlay, TextOverlayController
from core.transform_controller import TransformController
from ui.export_mixin import ExportMixin
from ui.warp_support import LiveWarpPreviewThread, MeshWarpApplyThread
from ui.transform_view import ImageGraphicsView


class MainWindow(ExportMixin, FluentWindow):
    PANEL_KEYS = ["crop", "transform", "mesh", "perspective", "text", "export"]

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("形绘")
        self.resize(1640, 980)

        self.image_model = ImageModel()
        self.history_manager = HistoryManager()
        self.crop_controller = CropController()
        self.transform_controller = TransformController()
        self.mesh_controller = MeshWarpController()
        self.perspective_controller = PerspectiveController()
        self.text_controller = TextOverlayController()

        self.current_mode = "crop"
        self._syncing_transform_inputs = False
        self._preview_rendering = False
        self._preview_pending = False
        self._preview_generation = 0
        self._mesh_dragging = False
        self._perspective_dragging = False
        self._selected_text_index: Optional[int] = None
        self._syncing_text_list = False
        self._model_download_thread = None
        self._export_thread = None
        self._export_progress_dialog = None
        self._export_preview_cache_key: Optional[tuple] = None
        self._export_preview_cache_image: Optional[Image.Image] = None
        self._live_preview_thread = None
        self._mesh_apply_thread = None
        self._mesh_apply_dialog = None

        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._render_live_preview)

        self.view = ImageGraphicsView()
        self.view.set_text_controller(self.text_controller)
        self.view.file_dropped.connect(self.load_image)
        self.view.crop_rect_changed.connect(self._update_crop_info)
        self.view.mesh_points_changed.connect(self._schedule_live_preview)
        self.view.perspective_points_changed.connect(self._schedule_live_preview)
        self.view.mesh_drag_state_changed.connect(self._set_mesh_dragging)
        self.view.perspective_drag_state_changed.connect(self._set_perspective_dragging)
        self.view.text_drag_started.connect(self._select_text_overlay)
        self.view.text_drag_finished.connect(self._handle_text_drag_finished)

        self.workbench = self._build_workbench()
        self.workbench.setObjectName("workbench_page")
        self.addSubInterface(self.workbench, FluentIcon.PHOTO, "工作台")

        self._update_actions_state()
        self._update_status("等待导入图片。")

    def _build_workbench(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        canvas_card = CardWidget()
        canvas_layout = QVBoxLayout(canvas_card)
        canvas_layout.setContentsMargins(18, 18, 18, 18)
        canvas_layout.setSpacing(12)

        title_row = QHBoxLayout()
        title_row.addWidget(SubtitleLabel("编辑工作台"))
        title_row.addStretch(1)
        self.open_button = PrimaryPushButton("打开图片")
        self.open_button.clicked.connect(self.open_image_dialog)
        self.export_button = PushButton("导出结果")
        self.export_button.clicked.connect(self.export_image_dialog)
        title_row.addWidget(self.open_button)
        title_row.addWidget(self.export_button)
        canvas_layout.addLayout(title_row)

        desc = BodyLabel("左侧导航只切换右侧控制面板，画布始终保持可见。")
        desc.setWordWrap(True)
        canvas_layout.addWidget(desc)

        self.mode_segment = SegmentedWidget()
        for key, label in [
            ("crop", "裁剪"),
            ("transform", "变换"),
            ("mesh", "网格"),
            ("perspective", "透视"),
            ("text", "文字"),
            ("export", "导出"),
        ]:
            self.mode_segment.addItem(key, label, onClick=lambda checked=True, m=key: self._activate_panel(m))
        self.mode_segment.setCurrentItem("crop")
        canvas_layout.addWidget(self.mode_segment)
        canvas_layout.addWidget(self.view, 1)

        self.right_card = CardWidget()
        self.right_card.setMinimumWidth(340)
        self.right_card.setMaximumWidth(460)
        self.right_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        right_layout = QVBoxLayout(self.right_card)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(12)

        self.status_label = BodyLabel("等待导入图片。")
        self.status_label.setObjectName("panelStatusLabel")
        self.status_label.setWordWrap(True)
        right_layout.addWidget(self.status_label)

        history_row = QHBoxLayout()
        self.undo_button = PushButton("撤销")
        self.undo_button.clicked.connect(self.undo)
        self.redo_button = PushButton("重做")
        self.redo_button.clicked.connect(self.redo)
        history_row.addWidget(self.undo_button)
        history_row.addWidget(self.redo_button)
        right_layout.addLayout(history_row)

        self.panel_stack = QStackedWidget()
        self.panel_pages = {
            "crop": self._build_crop_panel(),
            "transform": self._build_transform_panel(),
            "mesh": self._build_mesh_panel(),
            "perspective": self._build_perspective_panel(),
            "text": self._build_text_panel(),
            "export": self._build_export_panel(),
        }
        for key in self.PANEL_KEYS:
            self.panel_stack.addWidget(self.panel_pages[key])
        self.panel_scroll_area = QScrollArea()
        self.panel_scroll_area.setWidgetResizable(True)
        self.panel_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.panel_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.panel_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.panel_scroll_area.setWidget(self.panel_stack)
        right_layout.addWidget(self.panel_scroll_area, 1)

        layout.addWidget(canvas_card, 5)
        layout.addWidget(self.right_card, 2)
        self._apply_panel_styles()
        return page

    def _build_crop_panel(self) -> QWidget:
        page = QWidget()
        layout = self._panel_layout(page, "裁剪")
        self.crop_ratio_combo = ComboBox()
        self.crop_ratio_combo.addItems(["自由", "1:1", "4:3", "16:9"])
        self.crop_ratio_combo.currentTextChanged.connect(self._apply_crop_ratio)
        layout.addWidget(BodyLabel("比例"))
        layout.addWidget(self.crop_ratio_combo)
        self.crop_info_label = BodyLabel("区域：-")
        self.crop_info_label.setWordWrap(True)
        layout.addWidget(self.crop_info_label)
        row = QHBoxLayout()
        reset = PushButton("重置裁剪框")
        reset.clicked.connect(self._reset_crop)
        apply_btn = PrimaryPushButton("应用裁剪")
        apply_btn.clicked.connect(self.apply_crop)
        row.addWidget(reset)
        row.addWidget(apply_btn)
        layout.addLayout(row)
        layout.addStretch(1)
        return page

    def _build_transform_panel(self) -> QWidget:
        page = QWidget()
        layout = self._panel_layout(page, "缩放 / 拉伸 / 旋转")

        self.width_spin = SpinBox()
        self.height_spin = SpinBox()
        self.keep_ratio_switch = SwitchButton()
        self.rotate_spin = DoubleSpinBox()
        self.rotate_slider = Slider(Qt.Orientation.Horizontal)
        self.rotate_expand_switch = SwitchButton()
        self.transform_info_label = BodyLabel("当前尺寸：-")

        self.width_spin.setRange(1, 20000)
        self.height_spin.setRange(1, 20000)
        self.width_spin.valueChanged.connect(self._sync_transform_dimensions)
        self.height_spin.valueChanged.connect(self._sync_transform_dimensions)
        self.keep_ratio_switch.setChecked(True)

        self.rotate_spin.setRange(-360.0, 360.0)
        self.rotate_spin.setValue(0.0)
        self.rotate_spin.setDecimals(1)
        self.rotate_slider.setRange(-180, 180)
        self.rotate_slider.valueChanged.connect(lambda value: self.rotate_spin.setValue(float(value)))
        self.rotate_spin.valueChanged.connect(lambda value: self.rotate_slider.setValue(int(round(value))))
        self.rotate_expand_switch.setChecked(True)

        layout.addWidget(BodyLabel("宽度"))
        layout.addWidget(self.width_spin)
        layout.addWidget(BodyLabel("高度"))
        layout.addWidget(self.height_spin)
        layout.addWidget(BodyLabel("保持比例"))
        layout.addWidget(self.keep_ratio_switch)
        layout.addWidget(self.transform_info_label)

        quick_scale_row = QHBoxLayout()
        half_btn = PushButton("50%")
        half_btn.clicked.connect(lambda: self.apply_quick_scale(0.5))
        same_btn = PushButton("100%")
        same_btn.clicked.connect(lambda: self.apply_quick_scale(1.0))
        double_btn = PushButton("200%")
        double_btn.clicked.connect(lambda: self.apply_quick_scale(2.0))
        quick_scale_row.addWidget(half_btn)
        quick_scale_row.addWidget(same_btn)
        quick_scale_row.addWidget(double_btn)
        layout.addWidget(BodyLabel("快速缩放"))
        layout.addLayout(quick_scale_row)

        resize_btn = PrimaryPushButton("等比缩放")
        resize_btn.clicked.connect(self.apply_resize)
        stretch_btn = PushButton("自由拉伸")
        stretch_btn.clicked.connect(self.apply_stretch)
        resize_row = self._two_column_button_grid(resize_btn, stretch_btn)
        layout.addLayout(resize_row)

        swap_btn = PushButton("宽高互换")
        swap_btn.clicked.connect(self.swap_transform_dimensions)
        mesh_btn = PushButton("进入网格")
        mesh_btn.clicked.connect(self.apply_transform_and_enter_mesh)
        helper_row = self._two_column_button_grid(swap_btn, mesh_btn)
        layout.addLayout(helper_row)

        layout.addWidget(StrongBodyLabel("旋转"))
        layout.addWidget(BodyLabel("角度"))
        layout.addWidget(self.rotate_spin)
        layout.addWidget(self.rotate_slider)
        layout.addWidget(BodyLabel("扩展画布"))
        layout.addWidget(self.rotate_expand_switch)
        left_btn = PushButton("左转 90°")
        left_btn.clicked.connect(lambda: self.apply_rotate_preset(-90))
        right_btn = PushButton("右转 90°")
        right_btn.clicked.connect(lambda: self.apply_rotate_preset(90))
        rotate_helper_row = self._two_column_button_grid(left_btn, right_btn)
        layout.addLayout(rotate_helper_row)
        rotate_btn = PrimaryPushButton("应用旋转")
        rotate_btn.clicked.connect(self.apply_rotate)
        layout.addWidget(rotate_btn)
        layout.addStretch(1)
        return page

    def _build_mesh_panel(self) -> QWidget:
        page = QWidget()
        layout = self._panel_layout(page, "网格变形")
        self.mesh_rows_spin = SpinBox()
        self.mesh_cols_spin = SpinBox()
        self.mesh_rows_spin.setRange(2, 8)
        self.mesh_cols_spin.setRange(2, 8)
        self.mesh_rows_spin.setValue(4)
        self.mesh_cols_spin.setValue(4)
        layout.addWidget(BodyLabel("行数"))
        layout.addWidget(self.mesh_rows_spin)
        layout.addWidget(BodyLabel("列数"))
        layout.addWidget(self.mesh_cols_spin)
        rebuild = PushButton("重建网格")
        rebuild.clicked.connect(self._rebuild_mesh_overlay)
        reset = PushButton("重置控制点")
        reset.clicked.connect(self._reset_mesh_points)
        row = self._two_column_button_grid(rebuild, reset)
        layout.addLayout(row)
        shrink = PushButton("收缩预设")
        shrink.clicked.connect(lambda: self.view.apply_mesh_preset(-0.22))
        bulge = PushButton("膨胀预设")
        bulge.clicked.connect(lambda: self.view.apply_mesh_preset(0.22))
        preset_row = self._two_column_button_grid(shrink, bulge)
        layout.addLayout(preset_row)
        self.mesh_info_label = BodyLabel("支持拖动内外网格点。预览会自动降采样并在后台刷新，弱机器更稳定。")
        self.mesh_info_label.setObjectName("panelHintLabel")
        self.mesh_info_label.setWordWrap(True)
        layout.addWidget(self.mesh_info_label)
        apply_btn = PrimaryPushButton("应用网格变形")
        apply_btn.clicked.connect(self.apply_mesh_warp)
        layout.addWidget(apply_btn)
        layout.addStretch(1)
        return page

    def _build_perspective_panel(self) -> QWidget:
        page = QWidget()
        layout = self._panel_layout(page, "透视变换")
        self.perspective_info_label = BodyLabel("拖拽四角定义要矫正的区域。")
        self.perspective_info_label.setObjectName("panelHintLabel")
        self.perspective_info_label.setWordWrap(True)
        layout.addWidget(self.perspective_info_label)
        reset = PushButton("重置四角")
        reset.clicked.connect(self._reset_perspective_points)
        apply_btn = PrimaryPushButton("应用透视变换")
        apply_btn.clicked.connect(self.apply_perspective)
        row = self._two_column_button_grid(reset, apply_btn)
        layout.addLayout(row)
        layout.addStretch(1)
        return page

    def _build_text_panel(self) -> QWidget:
        page = QWidget()
        layout = self._panel_layout(page, "文字图层")

        self.text_layer_list = ListWidget()
        self.text_layer_list.currentRowChanged.connect(self._select_text_overlay)
        layout.addWidget(BodyLabel("图层列表"))
        layout.addWidget(self.text_layer_list)

        self.text_toggle_visible_button = PushButton("切换显隐")
        self.text_toggle_visible_button.clicked.connect(self.toggle_selected_text_visibility)
        delete_btn = PushButton("删除当前图层")
        delete_btn.clicked.connect(self.delete_selected_text_overlay)
        layer_actions = self._two_column_button_grid(self.text_toggle_visible_button, delete_btn)
        layout.addLayout(layer_actions)

        self.text_input = TextEdit()
        self.text_input.setFixedHeight(90)
        self.text_input.setPlaceholderText("输入要添加到图片上的文字")
        layout.addWidget(BodyLabel("文字内容"))
        layout.addWidget(self.text_input)

        self.text_size_spin = SpinBox()
        self.text_size_spin.setRange(8, 300)
        self.text_size_spin.setValue(36)
        self.text_color_button = ColorPickerButton(QColor("#ffffff"), "文字颜色")
        self.text_bold_switch = SwitchButton()
        style_grid = QGridLayout()
        style_grid.setHorizontalSpacing(8)
        style_grid.setVerticalSpacing(8)
        style_grid.addWidget(BodyLabel("字号"), 0, 0)
        style_grid.addWidget(self.text_size_spin, 1, 0)
        style_grid.addWidget(BodyLabel("颜色"), 0, 1)
        style_grid.addWidget(self.text_color_button, 1, 1)
        style_grid.addWidget(BodyLabel("粗体"), 2, 0)
        style_grid.addWidget(self.text_bold_switch, 2, 1)
        layout.addLayout(style_grid)

        add_btn = PrimaryPushButton("新增文字图层")
        add_btn.clicked.connect(self.add_text_overlay)
        update_btn = PushButton("更新当前图层")
        update_btn.clicked.connect(self.update_selected_text_overlay)
        button_row = self._two_column_button_grid(add_btn, update_btn)
        layout.addLayout(button_row)

        self.text_status_label = BodyLabel("添加文字后可在画布上拖动位置。")
        self.text_status_label.setObjectName("panelHintLabel")
        self.text_status_label.setWordWrap(True)
        layout.addWidget(self.text_status_label)
        layout.addStretch(1)
        return page

    def _panel_layout(self, page: QWidget, title: str) -> QVBoxLayout:
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(SubtitleLabel(title))
        return layout

    def _two_column_button_grid(self, left: QWidget, right: QWidget) -> QGridLayout:
        layout = QGridLayout()
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(8)
        if hasattr(left, "setSizePolicy"):
            left.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if hasattr(right, "setSizePolicy"):
            right.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.setColumnStretch(0, 1)
        layout.addWidget(left, 0, 0)
        layout.addWidget(right, 1, 0)
        return layout

    def _apply_panel_styles(self) -> None:
        self.right_card.setStyleSheet(
            "background-color: #f4f7fb; border: 1px solid #d7dfeb; border-radius: 14px;"
        )
        self.panel_scroll_area.setStyleSheet("background: transparent; border: none;")
        self.status_label.setStyleSheet(
            "background-color: #eaf2ff; color: #17324d; border: 1px solid #bfd3f2; "
            "border-radius: 10px; padding: 10px 12px;"
        )
        hint_style = (
            "background-color: #fff7e8; color: #5e3b00; border: 1px solid #f0d6a6; "
            "border-radius: 10px; padding: 8px 10px;"
        )
        for label in [
            self.mesh_info_label,
            self.perspective_info_label,
            self.text_status_label,
            self.export_dnn_info_label,
            self.export_hint_label,
        ]:
            label.setStyleSheet(hint_style)
        for button in self.findChildren(PushButton):
            button.setMinimumHeight(36)
        for button in self.findChildren(PrimaryPushButton):
            button.setMinimumHeight(38)

    def _activate_panel(self, mode: str) -> None:
        self.current_mode = mode
        self.mode_segment.setCurrentItem(mode)
        self.panel_stack.setCurrentWidget(self.panel_pages[mode])
        self.panel_scroll_area.verticalScrollBar().setValue(0)
        if mode in {"crop", "mesh", "perspective"}:
            self.set_mode(mode)
        elif mode in {"transform", "text", "export"}:
            self._refresh_non_overlay_mode(mode)

    def _refresh_non_overlay_mode(self, mode: str) -> None:
        self.current_mode = mode
        self.preview_timer.stop()
        self._preview_generation += 1
        self._preview_pending = False
        self.image_model.clear_preview()
        self.view.set_image(self.image_model.display_image)
        self.view.set_preview_image(None)
        self.view.set_text_overlays(self.image_model.text_items)
        self.view.set_selected_text_index(self._selected_text_index)
        self.view.clear_overlays()
        self.view.set_editor_mode(mode)
        if mode == "export":
            self.update_export_comparison_preview()

    def open_image_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "打开图片", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.load_image(path)

    def load_image(self, path: str) -> None:
        try:
            image = self.image_model.load(path)
        except Exception as exc:
            self._show_error(f"无法打开图片：{exc}")
            return
        self._invalidate_export_preview_cache()
        self.history_manager.clear_with(image, self.image_model.text_items)
        self._selected_text_index = None
        self.view.set_image(self.image_model.display_image)
        self.view.set_text_overlays(self.image_model.text_items)
        self.view.set_selected_text_index(self._selected_text_index)
        self.view.fit_image()
        self._sync_dimension_inputs()
        self._refresh_panel_state()
        self._update_actions_state()
        self._update_status(f"已加载：{Path(path).name}  {image.width} × {image.height}")

    def set_mode(self, mode: str) -> None:
        self.current_mode = mode
        self.preview_timer.stop()
        self._preview_generation += 1
        self._preview_pending = False
        self.image_model.clear_preview()
        self.view.set_image(self.image_model.display_image)
        self.view.set_text_overlays(self.image_model.text_items)
        self.view.set_selected_text_index(self._selected_text_index)
        self.view.set_editor_mode(mode)
        self.view.clear_overlays()
        if mode == "crop":
            self.view.enter_crop_mode()
            self._apply_crop_ratio(self.crop_ratio_combo.currentText())
            self._update_crop_info()
        elif mode == "mesh":
            self.view.enter_mesh_mode(self.mesh_rows_spin.value(), self.mesh_cols_spin.value())
            self._schedule_live_preview()
        elif mode == "perspective":
            self.view.enter_perspective_mode()
            self._schedule_live_preview()

    def _refresh_panel_state(self) -> None:
        self._invalidate_export_preview_cache()
        if self.current_mode in {"crop", "mesh", "perspective"}:
            self.set_mode(self.current_mode)
        else:
            self._refresh_non_overlay_mode(self.current_mode)
        self._refresh_text_layer_list()
        if self.current_mode == "export":
            self.update_export_comparison_preview()

    def apply_crop(self) -> None:
        image = self.image_model.current_image
        if image is None:
            self._show_error("请先导入图片。")
            return
        crop_box = self.view.get_crop_box()
        if crop_box is None:
            self._show_error("当前没有可用的裁剪框。")
            return
        try:
            result = self.crop_controller.crop(image, crop_box)
        except Exception as exc:
            self._show_error(str(exc))
            return
        self.image_model.set_text_items(self.text_controller.crop_positions(self.image_model.text_items, crop_box, result.size))
        self._selected_text_index = None
        self._commit_image(result, "已应用裁剪。")

    def apply_resize(self) -> None:
        image = self.image_model.current_image
        if image is None:
            self._show_error("请先导入图片。")
            return
        result = self.transform_controller.resize_keep_aspect(image, self.width_spin.value())
        self.image_model.set_text_items(self.text_controller.scale_positions(self.image_model.text_items, image.size, result.size))
        self._commit_image(result, "已完成等比缩放。")

    def apply_stretch(self) -> None:
        image = self.image_model.current_image
        if image is None:
            self._show_error("请先导入图片。")
            return
        result = self.transform_controller.stretch(image, self.width_spin.value(), self.height_spin.value())
        self.image_model.set_text_items(self.text_controller.scale_positions(self.image_model.text_items, image.size, result.size))
        self._commit_image(result, "已完成自由拉伸。")

    def apply_transform_and_enter_mesh(self) -> None:
        self.apply_stretch()
        self._activate_panel("mesh")

    def apply_quick_scale(self, factor: float) -> None:
        image = self.image_model.current_image
        if image is None:
            self._show_error("请先导入图片。")
            return
        self.width_spin.setValue(max(1, round(image.width * factor)))
        if self.keep_ratio_switch.isChecked():
            self.apply_resize()
        else:
            self.height_spin.setValue(max(1, round(image.height * factor)))
            self.apply_stretch()

    def swap_transform_dimensions(self) -> None:
        width = self.width_spin.value()
        height = self.height_spin.value()
        self.width_spin.setValue(height)
        self.height_spin.setValue(width)

    def apply_rotate_preset(self, angle: float) -> None:
        self.rotate_spin.setValue(angle)
        self.apply_rotate()

    def apply_rotate(self) -> None:
        image = self.image_model.current_image
        if image is None:
            self._show_error("请先导入图片。")
            return
        angle = self.rotate_spin.value()
        expand = self.rotate_expand_switch.isChecked()
        result = self.transform_controller.rotate(image, angle, expand=expand)
        self.image_model.set_text_items(
            self.text_controller.rotate_positions(self.image_model.text_items, image.size, result.size, angle, expand)
        )
        self._selected_text_index = None
        self._commit_image(result, f"已旋转 {angle:.1f}°。")

    def apply_mesh_warp(self) -> None:
        image = self.image_model.current_image
        source_points = self.view.get_mesh_source_points()
        target_points = self.view.get_mesh_target_points()
        if image is None or source_points is None or target_points is None:
            self._show_error("请先进入网格变形模式。")
            return
        if self._mesh_apply_thread is not None and self._mesh_apply_thread.isRunning():
            self._show_error("当前已有网格变形任务正在计算，请稍候。")
            return

        dialog = QProgressDialog("正在后台计算网格变形…", "", 0, 0, self)
        dialog.setWindowTitle("网格变形")
        dialog.setCancelButton(None)
        dialog.setMinimumDuration(0)
        dialog.setAutoClose(False)
        dialog.setAutoReset(False)
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._mesh_apply_dialog = dialog

        self._mesh_apply_thread = MeshWarpApplyThread(image, source_points, target_points)
        self._mesh_apply_thread.warp_finished.connect(self._handle_mesh_apply_finished)
        self._mesh_apply_thread.warp_failed.connect(self._handle_mesh_apply_failed)
        self._mesh_apply_thread.finished.connect(self._cleanup_mesh_apply_task)
        self._mesh_apply_thread.start()
        dialog.show()
        self._update_status("正在后台计算网格变形…")

    def apply_perspective(self) -> None:
        image = self.image_model.current_image
        points = self.view.get_perspective_points()
        if image is None or points is None:
            self._show_error("请先进入透视模式。")
            return
        try:
            result = self.perspective_controller.warp(image, points, render_mode=self.perspective_controller.FINAL)
        except Exception as exc:
            self._show_error(f"透视变换失败：{exc}")
            return
        self._commit_image(result, "已应用透视变换。")

    def add_text_overlay(self) -> None:
        image = self.image_model.current_image
        text = self.text_input.toPlainText().strip()
        if image is None:
            self._show_error("请先导入图片。")
            return
        if not text:
            self._show_error("请输入文字内容。")
            return
        item = TextOverlay(
            text=text,
            x=image.width / 2 - 80,
            y=image.height / 2,
            font_size=self.text_size_spin.value(),
            color=self.text_color_button.color.name(),
            bold=self.text_bold_switch.isChecked(),
            visible=True,
        )
        self.image_model.text_items.append(item)
        self._invalidate_export_preview_cache()
        self._selected_text_index = len(self.image_model.text_items) - 1
        self._load_text_item_to_editor(item)
        self._update_text_preview()
        self.history_manager.record(self.image_model.current_image, self.image_model.text_items)
        self._update_actions_state()
        self._update_status("已添加文字图层，请在画布上拖动位置。")

    def update_selected_text_overlay(self) -> None:
        if self._selected_text_index is None or self._selected_text_index >= len(self.image_model.text_items):
            self._show_error("当前没有选中的文字图层。")
            return
        text = self.text_input.toPlainText().strip()
        if not text:
            self._show_error("请输入文字内容。")
            return
        item = self.image_model.text_items[self._selected_text_index]
        item.text = text
        item.font_size = self.text_size_spin.value()
        item.color = self.text_color_button.color.name()
        item.bold = self.text_bold_switch.isChecked()
        self._invalidate_export_preview_cache()
        self._update_text_preview()
        self.history_manager.record(self.image_model.current_image, self.image_model.text_items)
        self._update_actions_state()
        self._update_status("已更新文字图层。")

    def delete_selected_text_overlay(self) -> None:
        if self._selected_text_index is None or self._selected_text_index >= len(self.image_model.text_items):
            self._show_error("当前没有选中的文字图层。")
            return
        self.image_model.text_items.pop(self._selected_text_index)
        self._invalidate_export_preview_cache()
        self._selected_text_index = None
        self._update_text_preview()
        self.history_manager.record(self.image_model.current_image, self.image_model.text_items)
        self._update_actions_state()
        self._update_status("已删除文字图层。")

    def toggle_selected_text_visibility(self) -> None:
        if self._selected_text_index is None or self._selected_text_index >= len(self.image_model.text_items):
            self._show_error("当前没有选中的文字图层。")
            return
        item = self.image_model.text_items[self._selected_text_index]
        item.visible = not item.visible
        self._invalidate_export_preview_cache()
        self._update_text_preview()
        self.history_manager.record(self.image_model.current_image, self.image_model.text_items)
        self._update_actions_state()
        self._update_status("已切换图层显隐。")

    def undo(self) -> None:
        state = self.history_manager.undo()
        if state is None:
            return
        self._invalidate_export_preview_cache()
        self.image_model.set_current_image(state.image)
        self.image_model.set_text_items(state.text_items)
        self._selected_text_index = None
        self.view.set_image(self.image_model.display_image)
        self.view.set_text_overlays(self.image_model.text_items)
        self.view.set_selected_text_index(None)
        self._sync_dimension_inputs()
        self._refresh_panel_state()
        self._update_actions_state()
        self._update_status("已撤销。")

    def redo(self) -> None:
        state = self.history_manager.redo()
        if state is None:
            return
        self._invalidate_export_preview_cache()
        self.image_model.set_current_image(state.image)
        self.image_model.set_text_items(state.text_items)
        self._selected_text_index = None
        self.view.set_image(self.image_model.display_image)
        self.view.set_text_overlays(self.image_model.text_items)
        self.view.set_selected_text_index(None)
        self._sync_dimension_inputs()
        self._refresh_panel_state()
        self._update_actions_state()
        self._update_status("已重做。")

    def _commit_image(self, image: Image.Image, status_message: str) -> None:
        self.preview_timer.stop()
        self._preview_generation += 1
        self._preview_pending = False
        self._invalidate_export_preview_cache()
        self.image_model.set_current_image(image)
        self.history_manager.record(image, self.image_model.text_items)
        self.view.set_image(self.image_model.display_image)
        self.view.set_text_overlays(self.image_model.text_items)
        self.view.set_selected_text_index(self._selected_text_index)
        self.view.fit_image()
        self._sync_dimension_inputs()
        self._refresh_panel_state()
        self._update_actions_state()
        self._update_status(status_message)

    def _refresh_text_layer_list(self) -> None:
        self._syncing_text_list = True
        self.text_layer_list.clear()
        for index, item in enumerate(self.image_model.text_items):
            prefix = "👁" if item.visible else "🚫"
            self.text_layer_list.addItem(f"{prefix} {index + 1}. {item.text[:20] or '空文字'}")
        if self._selected_text_index is not None and self._selected_text_index < self.text_layer_list.count():
            self.text_layer_list.setCurrentRow(self._selected_text_index)
        self._syncing_text_list = False
        self.text_status_label.setText(f"当前文字图层：{len(self.image_model.text_items)} 个")

    def _select_text_overlay(self, index: int) -> None:
        if self._syncing_text_list:
            return
        if not (0 <= index < len(self.image_model.text_items)):
            return
        self._selected_text_index = index
        self._load_text_item_to_editor(self.image_model.text_items[index])
        self.view.set_selected_text_index(index)
        self.text_status_label.setText(f"已选中文字图层 #{index + 1}")

    def _handle_text_drag_finished(self, index: int) -> None:
        self._selected_text_index = index
        self.view.set_selected_text_index(index)
        self._refresh_text_layer_list()
        if self.image_model.current_image is not None:
            self.history_manager.record(self.image_model.current_image, self.image_model.text_items)
            self._update_actions_state()
        self.text_status_label.setText("已更新文字位置。")

    def _load_text_item_to_editor(self, item: TextOverlay) -> None:
        self.text_input.setPlainText(item.text)
        self.text_size_spin.setValue(item.font_size)
        self.text_color_button.setColor(QColor(item.color))
        self.text_bold_switch.setChecked(item.bold)

    def _schedule_live_preview(self) -> None:
        if self.image_model.current_image is None or self.current_mode not in {"mesh", "perspective"}:
            return
        if self._is_dragging_active():
            self._preview_pending = True
            return
        self._preview_pending = True
        self._preview_generation += 1
        self.preview_timer.start(120 if self.current_mode == "mesh" else 60)

    def _render_live_preview(self) -> None:
        if self._preview_rendering or self._is_dragging_active():
            self._preview_pending = True
            return
        image = self.image_model.current_image
        if image is None or self.current_mode not in {"mesh", "perspective"}:
            return
        generation = self._preview_generation
        self._preview_pending = False
        mode = self.current_mode
        if mode == "mesh":
            source_points = self.view.get_mesh_source_points()
            target_points = self.view.get_mesh_target_points()
            if source_points is None or target_points is None:
                return
            thread = LiveWarpPreviewThread(
                image,
                mode="mesh",
                generation=generation,
                preview_max_side=420,
                source_points=source_points,
                target_points=target_points,
            )
        else:
            points = self.view.get_perspective_points()
            if points is None:
                return
            thread = LiveWarpPreviewThread(
                image,
                mode="perspective",
                generation=generation,
                preview_max_side=720,
                perspective_points=points,
            )
        self._preview_rendering = True
        self._live_preview_thread = thread
        thread.preview_ready.connect(self._handle_live_preview_ready)
        thread.preview_failed.connect(self._handle_live_preview_failed)
        thread.finished.connect(self._handle_live_preview_complete)
        thread.start()

    def _handle_live_preview_ready(self, generation: int, preview_image: Image.Image, display_size: tuple[int, int]) -> None:
        if generation != self._preview_generation:
            return
        if self.image_model.current_image is None or self.current_mode not in {"mesh", "perspective"}:
            return
        self.view.set_preview_image(preview_image, display_size=display_size)

    def _handle_live_preview_failed(self, generation: int, message: str) -> None:
        if generation != self._preview_generation:
            return
        self._update_status(f"预览刷新失败：{message}")

    def _handle_live_preview_complete(self) -> None:
        self._preview_rendering = False
        self._live_preview_thread = None
        if self._preview_pending and not self._is_dragging_active():
            self.preview_timer.start(10)

    def _handle_mesh_apply_finished(self, image: Image.Image) -> None:
        if self._mesh_apply_dialog is not None:
            self._mesh_apply_dialog.close()
        self._commit_image(image, "已应用网格变形。")

    def _handle_mesh_apply_failed(self, message: str) -> None:
        if self._mesh_apply_dialog is not None:
            self._mesh_apply_dialog.close()
        self._show_error(f"网格变形失败：{message}")
        self._update_status(f"网格变形失败：{message}")

    def _cleanup_mesh_apply_task(self) -> None:
        if self._mesh_apply_dialog is not None:
            self._mesh_apply_dialog.close()
            self._mesh_apply_dialog = None
        self._mesh_apply_thread = None

    def _update_text_preview(self) -> None:
        self.view.set_text_overlays(self.image_model.text_items)
        self.view.set_selected_text_index(self._selected_text_index)
        self._refresh_text_layer_list()

    def _apply_crop_ratio(self, text: str) -> None:
        ratios = {"自由": None, "1:1": 1.0, "4:3": 4 / 3, "16:9": 16 / 9}
        self.view.set_crop_aspect_ratio(ratios[text])
        self._update_crop_info()

    def _reset_crop(self) -> None:
        self.view.reset_crop_rect()
        self._update_crop_info()

    def _update_crop_info(self, rect=None) -> None:
        del rect
        crop_box = self.view.get_crop_box()
        if crop_box is None:
            self.crop_info_label.setText("区域：-")
            return
        left, top, right, bottom = crop_box
        self.crop_info_label.setText(f"区域：({left}, {top}) → ({right}, {bottom})  {right-left} × {bottom-top}")

    def _set_mesh_dragging(self, dragging: bool) -> None:
        self._mesh_dragging = dragging
        self._handle_drag_state_change()

    def _set_perspective_dragging(self, dragging: bool) -> None:
        self._perspective_dragging = dragging
        self._handle_drag_state_change()

    def _handle_drag_state_change(self) -> None:
        if self._is_dragging_active():
            self.preview_timer.stop()
            self._preview_generation += 1
            self.view.set_preview_image(None)
            return
        if self.current_mode in {"mesh", "perspective"}:
            self._schedule_live_preview()

    def _is_dragging_active(self) -> bool:
        if self.current_mode == "mesh":
            return self._mesh_dragging
        if self.current_mode == "perspective":
            return self._perspective_dragging
        return False

    def _sync_transform_dimensions(self, value: int) -> None:
        del value
        if self._syncing_transform_inputs or not self.keep_ratio_switch.isChecked():
            return
        image = self.image_model.current_image
        if image is None:
            return
        self._syncing_transform_inputs = True
        if self.sender() is self.width_spin:
            self.height_spin.setValue(self.transform_controller.proportional_height(image, self.width_spin.value()))
        elif self.sender() is self.height_spin:
            self.width_spin.setValue(self.transform_controller.proportional_width(image, self.height_spin.value()))
        self._syncing_transform_inputs = False

    def _sync_dimension_inputs(self) -> None:
        image = self.image_model.current_image
        if image is None:
            self.transform_info_label.setText("当前尺寸：-")
            return
        self._syncing_transform_inputs = True
        self.width_spin.setValue(image.width)
        self.height_spin.setValue(image.height)
        self._syncing_transform_inputs = False
        self.transform_info_label.setText(f"当前尺寸：{image.width} × {image.height}")

    def _rebuild_mesh_overlay(self) -> None:
        self.set_mode("mesh")

    def _reset_mesh_points(self) -> None:
        self.view.reset_mesh_points()
        self._schedule_live_preview()

    def _reset_perspective_points(self) -> None:
        self.view.reset_perspective_points()
        self._schedule_live_preview()

    def _update_actions_state(self) -> None:
        self.undo_button.setEnabled(self.history_manager.can_undo)
        self.redo_button.setEnabled(self.history_manager.can_redo)

    def _update_status(self, message: str) -> None:
        self.status_label.setText(message)

    def _show_error(self, message: str) -> None:
        MessageBox("错误", message, self).exec()
