from __future__ import annotations

from dataclasses import dataclass

from PIL import Image
from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, PrimaryPushButton, PushButton, SubtitleLabel

from utils.image_utils import pil_to_qpixmap


@dataclass(frozen=True)
class RegionSelection:
    x: int
    y: int
    width: int
    height: int

    def as_payload(self) -> str:
        return f"{self.x},{self.y},{self.width},{self.height}"


class RegionCanvas(QLabel):
    selection_changed = Signal(object)

    def __init__(self, image: Image.Image, minimum_size: tuple[int, int] | None = None) -> None:
        super().__init__()
        self._image = image
        self._pixmap = pil_to_qpixmap(image)
        self._scale = 1.0
        self._selection_rect = QRect()
        self._saved_regions: list[RegionSelection] = []
        self._drag_origin = QPoint()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if minimum_size is None:
            minimum_size = (680, 420)
        self.setMinimumSize(*minimum_size)
        self.setMouseTracking(True)
        self._refresh_pixmap()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_pixmap()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        point = self._map_to_image(event.position().toPoint())
        if point is None:
            return
        self._drag_origin = point
        self._selection_rect = QRect(point, point)
        self.selection_changed.emit(self.current_selection())
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return super().mouseMoveEvent(event)
        point = self._map_to_image(event.position().toPoint())
        if point is None:
            return
        self._selection_rect = QRect(self._drag_origin, point).normalized()
        self.selection_changed.emit(self.current_selection())
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.selection_changed.emit(self.current_selection())
            self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        saved_pen = QPen(QColor("#1f7a44"))
        saved_pen.setWidth(2)
        painter.setPen(saved_pen)
        painter.setBrush(QColor(31, 122, 68, 38))
        for selection in self._saved_regions:
            painter.drawRect(self._map_from_image(selection))

        current = self.current_selection()
        if current is not None:
            active_pen = QPen(QColor("#e05a00"))
            active_pen.setWidth(3)
            painter.setPen(active_pen)
            painter.setBrush(QColor(224, 90, 0, 48))
            painter.drawRect(self._map_from_image(current))

    def current_selection(self) -> RegionSelection | None:
        rect = self._selection_rect.normalized()
        if rect.width() < 2 or rect.height() < 2:
            return None
        x = max(0, min(rect.left(), self._image.width - 1))
        y = max(0, min(rect.top(), self._image.height - 1))
        right = max(x + 1, min(rect.right(), self._image.width - 1))
        bottom = max(y + 1, min(rect.bottom(), self._image.height - 1))
        return RegionSelection(x=x, y=y, width=right - x + 1, height=bottom - y + 1)

    def saved_regions(self) -> list[RegionSelection]:
        return list(self._saved_regions)

    def set_saved_regions(self, regions: list[RegionSelection]) -> None:
        self._saved_regions = list(regions)
        self._selection_rect = QRect()
        self.selection_changed.emit(self.saved_regions())
        self.update()

    def add_current_selection(self) -> RegionSelection | None:
        selection = self.current_selection()
        if selection is None:
            return None
        self._saved_regions.append(selection)
        self._selection_rect = QRect()
        self.selection_changed.emit(self.saved_regions())
        self.update()
        return selection

    def clear_saved_regions(self) -> None:
        self._saved_regions.clear()
        self._selection_rect = QRect()
        self.selection_changed.emit(self.saved_regions())
        self.update()

    def combined_payload(self) -> str:
        regions = self.saved_regions()
        current = self.current_selection()
        if current is not None:
            regions.append(current)
        return ";".join(region.as_payload() for region in regions)

    def _refresh_pixmap(self) -> None:
        if self.width() <= 0 or self.height() <= 0:
            return
        scaled = self._pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self._scale = scaled.width() / max(1, self._image.width)
        self.setPixmap(scaled)

    def _map_to_image(self, point: QPoint) -> QPoint | None:
        pixmap = self.pixmap()
        if pixmap is None:
            return None
        x_offset = (self.width() - pixmap.width()) // 2
        y_offset = (self.height() - pixmap.height()) // 2
        local_x = point.x() - x_offset
        local_y = point.y() - y_offset
        if local_x < 0 or local_y < 0 or local_x >= pixmap.width() or local_y >= pixmap.height():
            return None
        image_x = int(local_x / max(self._scale, 1e-6))
        image_y = int(local_y / max(self._scale, 1e-6))
        image_x = max(0, min(image_x, self._image.width - 1))
        image_y = max(0, min(image_y, self._image.height - 1))
        return QPoint(image_x, image_y)

    def _map_from_image(self, selection: RegionSelection) -> QRect:
        pixmap = self.pixmap()
        if pixmap is None:
            return QRect()
        x_offset = (self.width() - pixmap.width()) // 2
        y_offset = (self.height() - pixmap.height()) // 2
        left = int(selection.x * self._scale) + x_offset
        top = int(selection.y * self._scale) + y_offset
        width = max(1, int(selection.width * self._scale))
        height = max(1, int(selection.height * self._scale))
        return QRect(left, top, width, height)


class RegionPickerDialog(QDialog):
    def __init__(self, image: Image.Image, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("选择修复区域")
        self.resize(860, 620)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        layout.addWidget(SubtitleLabel("框选修复区域"))
        hint = BodyLabel("在图片上拖拽选择区域，点击“添加当前区域”可累积多块区域，确认后会回填为 x,y,w,h;x,y,w,h。")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.canvas = RegionCanvas(image)
        layout.addWidget(self.canvas, 1)

        self.selection_label = BodyLabel("当前未选择区域。")
        self.selection_label.setWordWrap(True)
        layout.addWidget(self.selection_label)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        button_row.addStretch(1)
        add_button = PushButton("添加当前区域")
        add_button.clicked.connect(self._add_current_region)
        clear_button = PushButton("清空区域")
        clear_button.clicked.connect(self._clear_regions)
        cancel_button = PushButton("取消")
        cancel_button.clicked.connect(self.reject)
        confirm_button = PrimaryPushButton("使用当前区域")
        confirm_button.clicked.connect(self.accept)
        button_row.addWidget(add_button)
        button_row.addWidget(clear_button)
        button_row.addWidget(cancel_button)
        button_row.addWidget(confirm_button)
        layout.addLayout(button_row)

        self.canvas.selection_changed.connect(self._handle_selection_changed)

    def selected_region(self) -> RegionSelection | None:
        regions = self.selected_regions()
        return regions[-1] if regions else None

    def selected_regions(self) -> list[RegionSelection]:
        current = self.canvas.current_selection()
        regions = self.canvas.saved_regions()
        if current is not None:
            regions.append(current)
        return regions

    def combined_payload(self) -> str:
        return ";".join(region.as_payload() for region in self.selected_regions())

    def _add_current_region(self) -> None:
        self.canvas.add_current_selection()

    def _clear_regions(self) -> None:
        self.canvas.clear_saved_regions()

    def _handle_selection_changed(self, _selection) -> None:
        regions = self.selected_regions()
        if not regions:
            self.selection_label.setText("当前未选择区域。")
            return
        latest = regions[-1]
        self.selection_label.setText(
            f"当前区域数：{len(regions)}；最后一块：x={latest.x}, y={latest.y}, w={latest.width}, h={latest.height}"
        )
