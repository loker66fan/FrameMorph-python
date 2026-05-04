from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap, QTransform
from PySide6.QtWidgets import QApplication, QGraphicsPixmapItem, QGraphicsScene, QGraphicsTextItem, QGraphicsView, QWidget

from ui.crop_view import CropRectItem
from ui.warp_view import MeshGridOverlay, OverlayControlPoint, PerspectiveOverlay
from utils.image_utils import pil_to_qpixmap


class EditorOverlayWidget(QWidget):
    CONTROL_RADIUS = 6.0
    HIT_RADIUS = 12.0

    def __init__(self, view: "ImageGraphicsView") -> None:
        super().__init__(view.viewport())
        self.view = view
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self._active_mesh_point: Optional[tuple[int, int]] = None
        self._active_perspective_point: Optional[int] = None
        self._active_text_index: Optional[int] = None
        self._drag_scene_offset = QPointF()
        self.hide()

    def sync_geometry(self) -> None:
        self.setGeometry(self.view.viewport().rect())
        self.raise_()

    def refresh_visibility(self) -> None:
        should_show = (
            self.view.mesh_overlay is not None
            or self.view.perspective_overlay is not None
            or bool(self.view.text_overlays)
        )
        if should_show:
            self.sync_geometry()
            self.show()
            self.raise_()
        else:
            self.hide()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if self.view.mesh_overlay is not None:
            self._draw_mesh_overlay(painter)
        if self.view.perspective_overlay is not None:
            self._draw_perspective_overlay(painter)
        self._draw_text_overlays(painter)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() != Qt.MouseButton.LeftButton:
            event.ignore()
            return
        scene_pos = self.view.mapToScene(event.position().toPoint())

        mesh_hit = self._pick_mesh_point(scene_pos)
        if mesh_hit is not None and self.view.mesh_overlay is not None:
            row, col = mesh_hit
            point = self.view.mesh_overlay.control_point(row, col).as_qpointf()
            self._active_mesh_point = mesh_hit
            self._drag_scene_offset = point - scene_pos
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            QApplication.instance().installEventFilter(self)
            self.view.mesh_drag_state_changed.emit(True)
            event.accept()
            return

        perspective_hit = self._pick_perspective_point(scene_pos)
        if perspective_hit is not None and self.view.perspective_overlay is not None:
            point = self.view.perspective_overlay.control_point(perspective_hit).as_qpointf()
            self._active_perspective_point = perspective_hit
            self._drag_scene_offset = point - scene_pos
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            QApplication.instance().installEventFilter(self)
            self.view.perspective_drag_state_changed.emit(True)
            event.accept()
            return

        text_hit = self._pick_text_item(scene_pos)
        if text_hit is not None:
            item = self.view.text_overlays[text_hit]
            self._active_text_index = text_hit
            self._drag_scene_offset = QPointF(item.x, item.y) - scene_pos
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            QApplication.instance().installEventFilter(self)
            self.view.text_drag_started.emit(text_hit)
            event.accept()
            return

        event.ignore()

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._finish_drag()
            event.accept()
            return
        event.ignore()

    def eventFilter(self, watched, event):  # type: ignore[override]
        if self._active_mesh_point is None and self._active_perspective_point is None and self._active_text_index is None:
            return super().eventFilter(watched, event)
        if event.type() == event.Type.MouseMove:
            local_pos = self.mapFromGlobal(event.globalPosition().toPoint())
            self._drag_to(local_pos)
            return True
        if event.type() == event.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            local_pos = self.mapFromGlobal(event.globalPosition().toPoint())
            self._drag_to(local_pos)
            self._finish_drag()
            return True
        return super().eventFilter(watched, event)

    def _drag_to(self, local_pos: QPoint) -> None:
        scene_point = self.view.mapToScene(local_pos) + self._drag_scene_offset
        if self._active_mesh_point is not None and self.view.mesh_overlay is not None:
            row, col = self._active_mesh_point
            self.view.mesh_overlay.move_point(row, col, scene_point, emit_signal=False)
            self.update()
            return
        if self._active_perspective_point is not None and self.view.perspective_overlay is not None:
            self.view.perspective_overlay.move_point(self._active_perspective_point, scene_point, emit_signal=False)
            self.update()
            return
        if self._active_text_index is not None and self._active_text_index < len(self.view.text_overlays):
            item = self.view.text_overlays[self._active_text_index]
            item.x = scene_point.x()
            item.y = scene_point.y()
            self.update()

    def _finish_drag(self) -> None:
        if self._active_mesh_point is not None:
            self._active_mesh_point = None
            self._drag_scene_offset = QPointF()
            QApplication.instance().removeEventFilter(self)
            self.unsetCursor()
            if self.view.mesh_overlay is not None:
                self.view.mesh_overlay.notify_changed()
            self.view.mesh_drag_state_changed.emit(False)
            return
        if self._active_perspective_point is not None:
            self._active_perspective_point = None
            self._drag_scene_offset = QPointF()
            QApplication.instance().removeEventFilter(self)
            self.unsetCursor()
            if self.view.perspective_overlay is not None:
                self.view.perspective_overlay.notify_changed()
            self.view.perspective_drag_state_changed.emit(False)
            return
        if self._active_text_index is not None:
            index = self._active_text_index
            self._active_text_index = None
            self._drag_scene_offset = QPointF()
            QApplication.instance().removeEventFilter(self)
            self.unsetCursor()
            self.view.text_drag_finished.emit(index)

    def _draw_mesh_overlay(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#1abc9c"), 1.5))
        path = QPainterPath()
        for start, end in self.view.mesh_overlay.iter_segments():
            path.moveTo(self.view.mapFromScene(start))
            path.lineTo(self.view.mapFromScene(end))
        painter.drawPath(path)
        for row in range(self.view.mesh_overlay.rows + 1):
            for col in range(self.view.mesh_overlay.cols + 1):
                self._draw_control_point(painter, self.view.mesh_overlay.control_point(row, col))

    def _draw_perspective_overlay(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#e74c3c"), 2.0))
        polygon = [self.view.mapFromScene(point) for point in self.view.perspective_overlay.polygon_points()]
        if polygon:
            path = QPainterPath()
            path.moveTo(polygon[0])
            for point in polygon[1:]:
                path.lineTo(point)
            path.closeSubpath()
            painter.drawPath(path)
        for index in range(4):
            self._draw_control_point(painter, self.view.perspective_overlay.control_point(index))

    def _draw_text_overlays(self, painter: QPainter) -> None:
        if self.view.text_controller is None:
            return
        for index, item in enumerate(self.view.text_overlays):
            painter.setPen(QColor(item.color))
            painter.setFont(self.view.text_controller.build_font(item))
            painter.drawText(self.view.mapFromScene(QPointF(item.x, item.y)), item.text)
            if index == self.view.selected_text_index:
                bounds = self.view.text_controller.bounds(item)
                top_left = self.view.mapFromScene(bounds.topLeft())
                bottom_right = self.view.mapFromScene(bounds.bottomRight())
                painter.setPen(QPen(QColor("#ffffff"), 1.0, Qt.PenStyle.DashLine))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(QRectF(top_left, bottom_right).normalized())

    def _draw_control_point(self, painter: QPainter, point: OverlayControlPoint) -> None:
        center = self.view.mapFromScene(point.as_qpointf())
        painter.setPen(QPen(QColor("#ffffff"), 1.0))
        painter.setBrush(QColor(point.color))
        painter.drawEllipse(center, self.CONTROL_RADIUS, self.CONTROL_RADIUS)

    def _pick_mesh_point(self, scene_pos: QPointF) -> Optional[tuple[int, int]]:
        if self.view.mesh_overlay is None:
            return None
        best_hit = None
        best_distance = self.HIT_RADIUS * self.HIT_RADIUS
        for row in range(self.view.mesh_overlay.rows + 1):
            for col in range(self.view.mesh_overlay.cols + 1):
                point = self.view.mesh_overlay.control_point(row, col).as_qpointf()
                distance = self.view._distance_squared(scene_pos, point)
                if distance <= best_distance:
                    best_hit = (row, col)
                    best_distance = distance
        return best_hit

    def _pick_perspective_point(self, scene_pos: QPointF) -> Optional[int]:
        if self.view.perspective_overlay is None:
            return None
        best_hit = None
        best_distance = self.HIT_RADIUS * self.HIT_RADIUS
        for index in range(4):
            point = self.view.perspective_overlay.control_point(index).as_qpointf()
            distance = self.view._distance_squared(scene_pos, point)
            if distance <= best_distance:
                best_hit = index
                best_distance = distance
        return best_hit

    def _pick_text_item(self, scene_pos: QPointF) -> Optional[int]:
        if self.view.text_controller is None:
            return None
        for index in range(len(self.view.text_overlays) - 1, -1, -1):
            if self.view.text_controller.bounds(self.view.text_overlays[index]).contains(scene_pos):
                return index
        return None


class ImageGraphicsView(QGraphicsView):
    SCENE_PADDING = 48.0

    file_dropped = Signal(str)
    crop_rect_changed = Signal(QRectF)
    mesh_points_changed = Signal()
    perspective_points_changed = Signal()
    mesh_drag_state_changed = Signal(bool)
    perspective_drag_state_changed = Signal(bool)
    text_drag_started = Signal(int)
    text_drag_finished = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
            | QPainter.RenderHint.TextAntialiasing
        )
        self.setBackgroundBrush(QColor("#20242b"))
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self._middle_panning = False
        self._last_pan_pos: Optional[QPoint] = None

        self.scene_ref = QGraphicsScene(self)
        self.setScene(self.scene_ref)

        self.pixmap_item = QGraphicsPixmapItem()
        self.pixmap_item.setZValue(0)
        self.scene_ref.addItem(self.pixmap_item)

        self.preview_pixmap_item = QGraphicsPixmapItem()
        self.preview_pixmap_item.setZValue(1)
        self.preview_pixmap_item.hide()
        self.scene_ref.addItem(self.preview_pixmap_item)

        self.placeholder_item = QGraphicsTextItem("拖拽图片到这里，或点击工具栏“打开”")
        self.placeholder_item.setDefaultTextColor(QColor("#c8ccd4"))
        self.placeholder_item.setZValue(5)
        self.scene_ref.addItem(self.placeholder_item)

        self.crop_item: Optional[CropRectItem] = None
        self.mesh_overlay: Optional[MeshGridOverlay] = None
        self.perspective_overlay: Optional[PerspectiveOverlay] = None
        self.text_overlays = []
        self.text_controller = None
        self.selected_text_index: Optional[int] = None
        self._has_image = False
        self.editor_overlay = EditorOverlayWidget(self)

        self._update_placeholder_position()

    def set_image(self, image: Optional[Image.Image]) -> None:
        if image is None:
            self.pixmap_item.setPos(0, 0)
            self.pixmap_item.setPixmap(QPixmap())
            self.preview_pixmap_item.setPixmap(QPixmap())
            self.preview_pixmap_item.hide()
            self.scene_ref.setSceneRect(QRectF())
            self._has_image = False
            self._update_placeholder_position()
            self.placeholder_item.show()
            self.editor_overlay.refresh_visibility()
            self.viewport().update()
            return

        pixmap = pil_to_qpixmap(image)
        self.pixmap_item.setPos(self.SCENE_PADDING, self.SCENE_PADDING)
        self.pixmap_item.setPixmap(pixmap)
        self.preview_pixmap_item.setPixmap(QPixmap())
        self.preview_pixmap_item.hide()
        self.scene_ref.setSceneRect(
            QRectF(
                0,
                0,
                pixmap.width() + self.SCENE_PADDING * 2,
                pixmap.height() + self.SCENE_PADDING * 2,
            )
        )
        self._has_image = True
        self.placeholder_item.hide()
        self.editor_overlay.refresh_visibility()
        self.viewport().update()

    def set_preview_image(self, image: Optional[Image.Image], display_size: Optional[tuple[int, int]] = None) -> None:
        if image is None:
            self.preview_pixmap_item.setPixmap(QPixmap())
            self.preview_pixmap_item.setTransform(QTransform())
            self.preview_pixmap_item.hide()
            self.editor_overlay.update()
            self.viewport().update()
            return
        pixmap = pil_to_qpixmap(image)
        self.preview_pixmap_item.setPixmap(pixmap)
        self.preview_pixmap_item.setPos(self.pixmap_item.pos())
        if display_size is not None and pixmap.width() and pixmap.height():
            scale_x = display_size[0] / pixmap.width()
            scale_y = display_size[1] / pixmap.height()
            self.preview_pixmap_item.setTransform(QTransform.fromScale(scale_x, scale_y))
        else:
            self.preview_pixmap_item.setTransform(QTransform())
        self.preview_pixmap_item.show()
        self.editor_overlay.update()
        self.viewport().update()

    def set_text_overlays(self, items) -> None:
        self.text_overlays = list(items)
        self.editor_overlay.refresh_visibility()
        self.editor_overlay.update()
        self.viewport().update()

    def set_text_controller(self, controller) -> None:
        self.text_controller = controller

    def set_selected_text_index(self, index: Optional[int]) -> None:
        self.selected_text_index = index
        self.editor_overlay.update()
        self.viewport().update()

    def fit_image(self) -> None:
        if self.pixmap_item.pixmap().isNull():
            return
        self.resetTransform()
        self.fitInView(self.scene_ref.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def clear_overlays(self) -> None:
        self.leave_crop_mode()
        self.leave_mesh_mode()
        self.leave_perspective_mode()
        self.editor_overlay.refresh_visibility()

    def set_editor_mode(self, mode: str) -> None:
        del mode
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def enter_crop_mode(self) -> None:
        if not self._has_image:
            return
        self.leave_mesh_mode()
        self.leave_perspective_mode()
        if self.crop_item is None:
            bounds = self._image_bounds()
            rect = self._default_crop_rect()
            self.crop_item = CropRectItem(rect, bounds, on_changed=self.crop_rect_changed.emit)
            self.scene_ref.addItem(self.crop_item)
        self.crop_item.show()

    def leave_crop_mode(self) -> None:
        if self.crop_item is not None:
            self.scene_ref.removeItem(self.crop_item)
            self.crop_item = None

    def set_crop_aspect_ratio(self, ratio: Optional[float]) -> None:
        if self.crop_item is not None:
            self.crop_item.set_aspect_ratio(ratio)

    def reset_crop_rect(self) -> None:
        if self.crop_item is not None:
            self.crop_item.reset_rect(self._default_crop_rect())

    def get_crop_box(self) -> Optional[tuple[int, int, int, int]]:
        if self.crop_item is None:
            return None
        left, top, right, bottom = self.crop_item.get_crop_box()
        origin = self.pixmap_item.pos()
        return (
            int(round(left - origin.x())),
            int(round(top - origin.y())),
            int(round(right - origin.x())),
            int(round(bottom - origin.y())),
        )

    def enter_mesh_mode(self, rows: int, cols: int) -> None:
        if not self._has_image:
            return
        self.leave_crop_mode()
        self.leave_perspective_mode()
        self.mesh_overlay = MeshGridOverlay(self._image_bounds(), rows, cols, on_changed=self._handle_mesh_changed)
        self.editor_overlay.refresh_visibility()
        self.viewport().update()

    def leave_mesh_mode(self) -> None:
        self.mesh_overlay = None
        self.editor_overlay.refresh_visibility()
        self.viewport().update()

    def reset_mesh_points(self) -> None:
        if self.mesh_overlay is not None:
            self.mesh_overlay.reset_points()
            self.viewport().update()

    def apply_mesh_preset(self, strength: float) -> None:
        if self.mesh_overlay is not None:
            self.mesh_overlay.apply_radial_preset(strength)
            self.viewport().update()

    def get_mesh_source_points(self) -> Optional[np.ndarray]:
        if self.mesh_overlay is None:
            return None
        return self._scene_points_to_image(self.mesh_overlay.source_points.copy())

    def get_mesh_target_points(self) -> Optional[np.ndarray]:
        if self.mesh_overlay is None:
            return None
        return self._scene_points_to_image(self.mesh_overlay.current_points_array())

    def enter_perspective_mode(self) -> None:
        if not self._has_image:
            return
        self.leave_crop_mode()
        self.leave_mesh_mode()
        self.perspective_overlay = PerspectiveOverlay(self._image_bounds(), on_changed=self._handle_perspective_changed)
        self.editor_overlay.refresh_visibility()
        self.viewport().update()

    def leave_perspective_mode(self) -> None:
        self.perspective_overlay = None
        self.editor_overlay.refresh_visibility()
        self.viewport().update()

    def reset_perspective_points(self) -> None:
        if self.perspective_overlay is not None:
            self.perspective_overlay.reset_points()
            self.viewport().update()

    def get_perspective_points(self) -> Optional[np.ndarray]:
        if self.perspective_overlay is None:
            return None
        return self._scene_points_to_image(self.perspective_overlay.current_points_array())

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        urls = event.mimeData().urls()
        if any(self._is_supported_file(url.toLocalFile()) for url in urls):
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event) -> None:  # type: ignore[override]
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if self._is_supported_file(file_path):
                self.file_dropped.emit(file_path)
                event.acceptProposedAction()
                return
        event.ignore()

    def wheelEvent(self, event) -> None:  # type: ignore[override]
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.MiddleButton:
            self._middle_panning = True
            self._last_pan_pos = event.position().toPoint()
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._middle_panning and self._last_pan_pos is not None:
            delta = event.position().toPoint() - self._last_pan_pos
            self._last_pan_pos = event.position().toPoint()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.MiddleButton:
            self._middle_panning = False
            self._last_pan_pos = None
            self.viewport().unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._update_placeholder_position()
        self.editor_overlay.sync_geometry()

    def _handle_mesh_changed(self) -> None:
        self.mesh_points_changed.emit()
        self.editor_overlay.update()
        self.viewport().update()

    def _handle_perspective_changed(self) -> None:
        self.perspective_points_changed.emit()
        self.editor_overlay.update()
        self.viewport().update()

    def _image_bounds(self) -> QRectF:
        return self.pixmap_item.sceneBoundingRect()

    def _default_crop_rect(self) -> QRectF:
        bounds = self._image_bounds()
        margin_x = bounds.width() * 0.1
        margin_y = bounds.height() * 0.1
        return QRectF(
            bounds.left() + margin_x,
            bounds.top() + margin_y,
            max(20.0, bounds.width() - margin_x * 2),
            max(20.0, bounds.height() - margin_y * 2),
        )

    def _update_placeholder_position(self) -> None:
        rect = self.viewport().rect()
        scene_point = self.mapToScene(rect.center())
        self.placeholder_item.setPos(scene_point.x() - 120, scene_point.y() - 10)

    def _is_supported_file(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in {".png", ".jpg", ".jpeg"}

    def _distance_squared(self, a: QPointF, b: QPointF) -> float:
        delta_x = a.x() - b.x()
        delta_y = a.y() - b.y()
        return delta_x * delta_x + delta_y * delta_y

    def _scene_points_to_image(self, points: np.ndarray) -> np.ndarray:
        origin = self.pixmap_item.pos()
        converted = points.copy()
        converted[..., 0] -= origin.x()
        converted[..., 1] -= origin.y()
        return converted
