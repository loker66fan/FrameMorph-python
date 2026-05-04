from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QCursor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsRectItem


class CropRectItem(QGraphicsRectItem):
    HANDLE_SIZE = 10.0
    MIN_SIZE = 20.0

    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_RIGHT = "bottom_right"
    BOTTOM_LEFT = "bottom_left"

    def __init__(
        self,
        rect: QRectF,
        bounds_rect: QRectF,
        on_changed: Optional[Callable[[QRectF], None]] = None,
    ) -> None:
        super().__init__(rect)
        self._bounds_rect = QRectF(bounds_rect)
        self._on_changed = on_changed
        self._aspect_ratio: Optional[float] = None
        self._active_handle: Optional[str] = None
        self._move_rect = False
        self._press_scene_pos = QPointF()
        self._press_rect = QRectF(rect)

        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setZValue(20)
        self.setPen(QPen(QColor("#ffb000"), 2.0, Qt.PenStyle.DashLine))
        self.setBrush(QColor(255, 176, 0, 35))

    def set_aspect_ratio(self, ratio: Optional[float]) -> None:
        self._aspect_ratio = ratio
        if ratio:
            self.setRect(self._adjust_rect_to_ratio(self.rect(), ratio))
            self._emit_changed()

    def reset_rect(self, rect: QRectF) -> None:
        self.setRect(rect)
        self._emit_changed()

    def get_crop_box(self) -> tuple[int, int, int, int]:
        rect = self.rect().normalized()
        return (
            int(round(rect.left())),
            int(round(rect.top())),
            int(round(rect.right())),
            int(round(rect.bottom())),
        )

    def hoverMoveEvent(self, event) -> None:  # type: ignore[override]
        handle = self._handle_at(event.pos())
        cursor = Qt.CursorShape.SizeAllCursor
        if handle in {self.TOP_LEFT, self.BOTTOM_RIGHT}:
            cursor = Qt.CursorShape.SizeFDiagCursor
        elif handle in {self.TOP_RIGHT, self.BOTTOM_LEFT}:
            cursor = Qt.CursorShape.SizeBDiagCursor
        self.setCursor(QCursor(cursor))
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event) -> None:  # type: ignore[override]
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() != Qt.MouseButton.LeftButton:
            event.ignore()
            return
        self._active_handle = self._handle_at(event.pos())
        self._move_rect = self._active_handle is None and self.rect().contains(event.pos())
        self._press_scene_pos = event.scenePos()
        self._press_rect = QRectF(self.rect())
        event.accept()

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        delta = event.scenePos() - self._press_scene_pos
        if self._active_handle:
            rect = self._resize_from_handle(delta)
            self.setRect(rect)
            self._emit_changed()
            event.accept()
            return
        if self._move_rect:
            rect = QRectF(self._press_rect)
            rect.translate(delta)
            rect = self._clamp_translated_rect(rect)
            self.setRect(rect)
            self._emit_changed()
            event.accept()
            return
        event.ignore()

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        self._active_handle = None
        self._move_rect = False
        super().mouseReleaseEvent(event)

    def paint(self, painter: QPainter, option, widget=None) -> None:  # type: ignore[override]
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRect(self.rect())
        painter.setBrush(QColor("#ffffff"))
        for handle_rect in self._handle_rects().values():
            painter.drawRect(handle_rect)

    def boundingRect(self) -> QRectF:  # type: ignore[override]
        half = self.HANDLE_SIZE / 2 + self.pen().widthF()
        return self.rect().normalized().adjusted(-half, -half, half, half)

    def shape(self) -> QPainterPath:  # type: ignore[override]
        path = QPainterPath()
        path.addRect(self.rect().normalized())
        for handle_rect in self._handle_rects().values():
            path.addRect(handle_rect)
        return path

    def _emit_changed(self) -> None:
        if self._on_changed:
            self._on_changed(self.rect().normalized())

    def _handle_rects(self) -> dict[str, QRectF]:
        rect = self.rect().normalized()
        half = self.HANDLE_SIZE / 2
        return {
            self.TOP_LEFT: QRectF(rect.topLeft().x() - half, rect.topLeft().y() - half, self.HANDLE_SIZE, self.HANDLE_SIZE),
            self.TOP_RIGHT: QRectF(
                rect.topRight().x() - half,
                rect.topRight().y() - half,
                self.HANDLE_SIZE,
                self.HANDLE_SIZE,
            ),
            self.BOTTOM_RIGHT: QRectF(
                rect.bottomRight().x() - half,
                rect.bottomRight().y() - half,
                self.HANDLE_SIZE,
                self.HANDLE_SIZE,
            ),
            self.BOTTOM_LEFT: QRectF(
                rect.bottomLeft().x() - half,
                rect.bottomLeft().y() - half,
                self.HANDLE_SIZE,
                self.HANDLE_SIZE,
            ),
        }

    def _handle_at(self, point: QPointF) -> Optional[str]:
        for name, rect in self._handle_rects().items():
            if rect.contains(point):
                return name
        return None

    def _resize_from_handle(self, delta: QPointF) -> QRectF:
        rect = QRectF(self._press_rect)
        anchors = {
            self.TOP_LEFT: rect.bottomRight(),
            self.TOP_RIGHT: rect.bottomLeft(),
            self.BOTTOM_RIGHT: rect.topLeft(),
            self.BOTTOM_LEFT: rect.topRight(),
        }
        anchor = anchors[self._active_handle]
        moving_point = {
            self.TOP_LEFT: rect.topLeft(),
            self.TOP_RIGHT: rect.topRight(),
            self.BOTTOM_RIGHT: rect.bottomRight(),
            self.BOTTOM_LEFT: rect.bottomLeft(),
        }[self._active_handle] + delta

        if self._aspect_ratio:
            return self._resize_with_ratio(anchor, moving_point, self._active_handle, self._aspect_ratio)
        return self._resize_free(anchor, moving_point, self._active_handle)

    def _resize_free(self, anchor: QPointF, moving_point: QPointF, handle: str) -> QRectF:
        sign_x = -1 if handle in {self.TOP_LEFT, self.BOTTOM_LEFT} else 1
        sign_y = -1 if handle in {self.TOP_LEFT, self.TOP_RIGHT} else 1

        max_width = anchor.x() - self._bounds_rect.left() if sign_x < 0 else self._bounds_rect.right() - anchor.x()
        max_height = anchor.y() - self._bounds_rect.top() if sign_y < 0 else self._bounds_rect.bottom() - anchor.y()

        width = max(self.MIN_SIZE, min(abs(moving_point.x() - anchor.x()), max_width))
        height = max(self.MIN_SIZE, min(abs(moving_point.y() - anchor.y()), max_height))

        new_point = QPointF(anchor.x() + sign_x * width, anchor.y() + sign_y * height)
        return QRectF(anchor, new_point).normalized()

    def _resize_with_ratio(
        self,
        anchor: QPointF,
        moving_point: QPointF,
        handle: str,
        ratio: float,
    ) -> QRectF:
        sign_x = -1 if handle in {self.TOP_LEFT, self.BOTTOM_LEFT} else 1
        sign_y = -1 if handle in {self.TOP_LEFT, self.TOP_RIGHT} else 1

        raw_width = abs(moving_point.x() - anchor.x())
        raw_height = abs(moving_point.y() - anchor.y())

        if raw_width / ratio >= raw_height:
            width = max(self.MIN_SIZE, raw_width)
        else:
            width = max(self.MIN_SIZE, raw_height * ratio)

        max_width = anchor.x() - self._bounds_rect.left() if sign_x < 0 else self._bounds_rect.right() - anchor.x()
        max_height = anchor.y() - self._bounds_rect.top() if sign_y < 0 else self._bounds_rect.bottom() - anchor.y()
        width = min(width, max_width, max_height * ratio)
        width = max(self.MIN_SIZE, width)
        height = width / ratio

        new_point = QPointF(anchor.x() + sign_x * width, anchor.y() + sign_y * height)
        rect = QRectF(anchor, new_point).normalized()
        return self._clamp_translated_rect(rect)

    def _clamp_translated_rect(self, rect: QRectF) -> QRectF:
        clamped = QRectF(rect)
        if clamped.left() < self._bounds_rect.left():
            clamped.translate(self._bounds_rect.left() - clamped.left(), 0)
        if clamped.top() < self._bounds_rect.top():
            clamped.translate(0, self._bounds_rect.top() - clamped.top())
        if clamped.right() > self._bounds_rect.right():
            clamped.translate(self._bounds_rect.right() - clamped.right(), 0)
        if clamped.bottom() > self._bounds_rect.bottom():
            clamped.translate(0, self._bounds_rect.bottom() - clamped.bottom())
        return clamped

    def _adjust_rect_to_ratio(self, rect: QRectF, ratio: float) -> QRectF:
        rect = rect.normalized()
        center = rect.center()
        width = rect.width()
        height = width / ratio
        if height > rect.height():
            height = rect.height()
            width = height * ratio
        adjusted = QRectF(center.x() - width / 2, center.y() - height / 2, width, height)
        return self._clamp_translated_rect(adjusted)
