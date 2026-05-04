from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Iterable

from PIL import Image
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QImage, QPainter

from utils.image_utils import pil_to_qimage, qimage_to_pil


@dataclass
class TextOverlay:
    text: str
    x: float
    y: float
    font_size: int = 32
    color: str = "#ffffff"
    bold: bool = False
    visible: bool = True

    def copy(self) -> "TextOverlay":
        return deepcopy(self)


class TextOverlayController:
    def clone_items(self, items: Iterable[TextOverlay]) -> list[TextOverlay]:
        return [item.copy() for item in items]

    def render(self, image: Image.Image, items: Iterable[TextOverlay]) -> Image.Image:
        qimage = pil_to_qimage(image)
        painter = QPainter(qimage)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        for item in items:
            if not item.visible or not item.text.strip():
                continue
            font = self.build_font(item)
            painter.setFont(font)
            painter.setPen(QColor(item.color))
            painter.drawText(QPointF(item.x, item.y), item.text)
        painter.end()
        return qimage_to_pil(qimage, image.mode)

    def bounds(self, item: TextOverlay) -> QRectF:
        font = self.build_font(item)
        metrics = QFontMetricsF(font)
        rect = metrics.boundingRect(item.text)
        rect.moveBottomLeft(QPointF(item.x, item.y))
        return rect

    def build_font(self, item: TextOverlay) -> QFont:
        font = QFont()
        font.setPointSize(max(1, int(item.font_size)))
        font.setBold(item.bold)
        return font

    def scale_positions(
        self,
        items: Iterable[TextOverlay],
        old_size: tuple[int, int],
        new_size: tuple[int, int],
    ) -> list[TextOverlay]:
        old_width, old_height = old_size
        new_width, new_height = new_size
        if old_width <= 0 or old_height <= 0:
            return self.clone_items(items)
        scale_x = new_width / old_width
        scale_y = new_height / old_height
        scaled: list[TextOverlay] = []
        for item in items:
            scaled.append(
                TextOverlay(
                    text=item.text,
                    x=item.x * scale_x,
                    y=item.y * scale_y,
                    font_size=max(1, round(item.font_size * min(scale_x, scale_y))),
                    color=item.color,
                    bold=item.bold,
                    visible=item.visible,
                )
            )
        return scaled

    def crop_positions(
        self,
        items: Iterable[TextOverlay],
        crop_box: tuple[int, int, int, int],
        new_size: tuple[int, int],
    ) -> list[TextOverlay]:
        left, top, _, _ = crop_box
        width, height = new_size
        cropped: list[TextOverlay] = []
        for item in items:
            new_x = item.x - left
            new_y = item.y - top
            if 0 <= new_x <= width and 0 <= new_y <= height:
                cropped.append(
                    TextOverlay(
                        text=item.text,
                        x=new_x,
                        y=new_y,
                        font_size=item.font_size,
                        color=item.color,
                        bold=item.bold,
                        visible=item.visible,
                    )
                )
        return cropped

    def rotate_positions(
        self,
        items: Iterable[TextOverlay],
        old_size: tuple[int, int],
        new_size: tuple[int, int],
        angle_degrees: float,
        expand: bool = True,
    ) -> list[TextOverlay]:
        old_width, old_height = old_size
        new_width, new_height = new_size
        angle_radians = angle_degrees * 3.141592653589793 / 180.0
        cos_theta = __import__("math").cos(angle_radians)
        sin_theta = __import__("math").sin(angle_radians)

        old_center = QPointF(old_width / 2, old_height / 2)
        new_center = QPointF(new_width / 2, new_height / 2) if expand else old_center

        rotated: list[TextOverlay] = []
        for item in items:
            dx = item.x - old_center.x()
            dy = item.y - old_center.y()
            new_x = dx * cos_theta - dy * sin_theta + new_center.x()
            new_y = dx * sin_theta + dy * cos_theta + new_center.y()
            if 0 <= new_x <= new_width and 0 <= new_y <= new_height:
                rotated.append(
                    TextOverlay(
                        text=item.text,
                        x=new_x,
                        y=new_y,
                        font_size=item.font_size,
                        color=item.color,
                        bold=item.bold,
                        visible=item.visible,
                    )
                )
        return rotated
