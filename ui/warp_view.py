from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np
from PySide6.QtCore import QPointF, QRectF


@dataclass
class OverlayControlPoint:
    x: float
    y: float
    color: str

    def as_qpointf(self) -> QPointF:
        return QPointF(self.x, self.y)


class MeshGridOverlay:
    MIN_GAP = 8.0
    MIN_AREA = 24.0

    def __init__(
        self,
        bounds_rect: QRectF,
        rows: int,
        cols: int,
        on_changed: Optional[Callable[[], None]] = None,
    ) -> None:
        self.bounds_rect = QRectF(bounds_rect)
        self.rows = rows
        self.cols = cols
        self.on_changed = on_changed

        self.source_points = self._build_regular_grid()
        self._point_cache = self.source_points.copy()

    def reset_points(self) -> None:
        self._point_cache = self.source_points.copy()
        self._emit_changed()

    def apply_radial_preset(self, strength: float) -> None:
        center = self.bounds_rect.center()
        max_radius = max(1.0, min(self.bounds_rect.width(), self.bounds_rect.height()) / 2)
        for row in range(self.rows + 1):
            for col in range(self.cols + 1):
                point = self._point_cache[row, col]
                delta_x = float(point[0] - center.x())
                delta_y = float(point[1] - center.y())
                distance = (delta_x**2 + delta_y**2) ** 0.5
                falloff = 1.0 - min(1.0, distance / max_radius)
                candidate = QPointF(
                    float(point[0] + delta_x * strength * falloff),
                    float(point[1] + delta_y * strength * falloff),
                )
                self.move_point(row, col, candidate, emit_signal=False)
        self._emit_changed()

    def current_points_array(self) -> np.ndarray:
        return self._point_cache.copy()

    def control_point(self, row: int, col: int) -> OverlayControlPoint:
        color = "#1abc9c" if not self.is_boundary_point(row, col) else "#95a5a6"
        point = self._point_cache[row, col]
        return OverlayControlPoint(float(point[0]), float(point[1]), color)

    def move_point(self, row: int, col: int, candidate: QPointF, emit_signal: bool = True) -> None:
        constrained = self._constrain_point_position(row, col, candidate)
        self._point_cache[row, col] = (constrained.x(), constrained.y())
        if emit_signal:
            self._emit_changed()

    def notify_changed(self) -> None:
        self._emit_changed()

    def is_boundary_point(self, row: int, col: int) -> bool:
        return row in {0, self.rows} or col in {0, self.cols}

    def iter_segments(self) -> list[tuple[QPointF, QPointF]]:
        segments: list[tuple[QPointF, QPointF]] = []
        for row in range(self.rows + 1):
            for col in range(self.cols):
                start = self._to_qpointf(self._point_cache[row, col])
                end = self._to_qpointf(self._point_cache[row, col + 1])
                segments.append((start, end))
        for col in range(self.cols + 1):
            for row in range(self.rows):
                start = self._to_qpointf(self._point_cache[row, col])
                end = self._to_qpointf(self._point_cache[row + 1, col])
                segments.append((start, end))
        return segments

    def _build_regular_grid(self) -> np.ndarray:
        x_coords = np.linspace(self.bounds_rect.left(), self.bounds_rect.right(), self.cols + 1, dtype=np.float32)
        y_coords = np.linspace(self.bounds_rect.top(), self.bounds_rect.bottom(), self.rows + 1, dtype=np.float32)
        grid_x, grid_y = np.meshgrid(x_coords, y_coords)
        return np.dstack((grid_x, grid_y)).astype(np.float32)

    def _constrain_point_position(self, row: int, col: int, candidate: QPointF) -> QPointF:
        constrained = QPointF(candidate)
        constrained.setX(min(self.bounds_rect.right(), max(self.bounds_rect.left(), constrained.x())))
        constrained.setY(min(self.bounds_rect.bottom(), max(self.bounds_rect.top(), constrained.y())))

        if col > 0:
            constrained.setX(max(constrained.x(), float(self._point_cache[row, col - 1, 0]) + self.MIN_GAP))
        if col < self.cols:
            constrained.setX(min(constrained.x(), float(self._point_cache[row, col + 1, 0]) - self.MIN_GAP))
        if row > 0:
            constrained.setY(max(constrained.y(), float(self._point_cache[row - 1, col, 1]) + self.MIN_GAP))
        if row < self.rows:
            constrained.setY(min(constrained.y(), float(self._point_cache[row + 1, col, 1]) - self.MIN_GAP))

        if self._position_keeps_local_quads_valid(row, col, constrained):
            return constrained
        return self._find_last_valid_position(row, col, self._to_qpointf(self._point_cache[row, col]), constrained)

    def _find_last_valid_position(
        self,
        row: int,
        col: int,
        start: QPointF,
        target: QPointF,
        iterations: int = 14,
    ) -> QPointF:
        low = QPointF(start)
        high = QPointF(target)
        for _ in range(iterations):
            mid = QPointF((low.x() + high.x()) * 0.5, (low.y() + high.y()) * 0.5)
            if self._position_keeps_local_quads_valid(row, col, mid):
                low = mid
            else:
                high = mid
        return low

    def _position_keeps_local_quads_valid(self, row: int, col: int, candidate: QPointF) -> bool:
        quad_row_start = max(0, row - 1)
        quad_row_end = min(self.rows - 1, row)
        quad_col_start = max(0, col - 1)
        quad_col_end = min(self.cols - 1, col)

        for quad_row in range(quad_row_start, quad_row_end + 1):
            for quad_col in range(quad_col_start, quad_col_end + 1):
                quad = self._build_quad_points(quad_row, quad_col, row, col, candidate)
                if not self._is_quad_valid(quad):
                    return False
        return True

    def _build_quad_points(
        self,
        quad_row: int,
        quad_col: int,
        moving_row: int,
        moving_col: int,
        candidate: QPointF,
    ) -> np.ndarray:
        corners = [
            (quad_row, quad_col),
            (quad_row, quad_col + 1),
            (quad_row + 1, quad_col + 1),
            (quad_row + 1, quad_col),
        ]
        quad = np.zeros((4, 2), dtype=np.float32)
        for index, (row, col) in enumerate(corners):
            if row == moving_row and col == moving_col:
                quad[index] = (candidate.x(), candidate.y())
            else:
                quad[index] = self._point_cache[row, col]
        return quad

    def _is_quad_valid(self, quad: np.ndarray) -> bool:
        if self._polygon_area(quad) < self.MIN_AREA:
            return False
        cross_values = []
        for index in range(4):
            a = quad[index]
            b = quad[(index + 1) % 4]
            c = quad[(index + 2) % 4]
            cross_values.append((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
        return all(value > 0 for value in cross_values) or all(value < 0 for value in cross_values)

    def _polygon_area(self, points: np.ndarray) -> float:
        x = points[:, 0]
        y = points[:, 1]
        return float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) * 0.5)

    def _emit_changed(self) -> None:
        if self.on_changed:
            self.on_changed()

    def _to_qpointf(self, point: np.ndarray) -> QPointF:
        return QPointF(float(point[0]), float(point[1]))


class PerspectiveOverlay:
    COLORS = ["#e74c3c", "#e67e22", "#f1c40f", "#3498db"]

    def __init__(
        self,
        bounds_rect: QRectF,
        on_changed: Optional[Callable[[], None]] = None,
    ) -> None:
        self.bounds_rect = QRectF(bounds_rect)
        self.on_changed = on_changed
        self._points = np.array(
            [
                [self.bounds_rect.left(), self.bounds_rect.top()],
                [self.bounds_rect.right(), self.bounds_rect.top()],
                [self.bounds_rect.right(), self.bounds_rect.bottom()],
                [self.bounds_rect.left(), self.bounds_rect.bottom()],
            ],
            dtype=np.float32,
        )

    def reset_points(self) -> None:
        self.__init__(self.bounds_rect, self.on_changed)
        self._emit_changed()

    def current_points_array(self) -> np.ndarray:
        return self._points.copy()

    def control_point(self, index: int) -> OverlayControlPoint:
        point = self._points[index]
        return OverlayControlPoint(float(point[0]), float(point[1]), self.COLORS[index])

    def move_point(self, index: int, candidate: QPointF, emit_signal: bool = True) -> None:
        candidate = QPointF(
            min(self.bounds_rect.right(), max(self.bounds_rect.left(), candidate.x())),
            min(self.bounds_rect.bottom(), max(self.bounds_rect.top(), candidate.y())),
        )
        self._points[index] = (candidate.x(), candidate.y())
        if emit_signal:
            self._emit_changed()

    def polygon_points(self) -> list[QPointF]:
        return [QPointF(float(point[0]), float(point[1])) for point in self._points]

    def notify_changed(self) -> None:
        self._emit_changed()

    def _emit_changed(self) -> None:
        if self.on_changed:
            self.on_changed()
