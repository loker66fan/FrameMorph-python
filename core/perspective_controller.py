from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

from utils.image_utils import cv_to_pil, pil_to_cv


class PerspectiveController:
    PREVIEW = "preview"
    FINAL = "final"

    def warp(self, image: Image.Image, source_points: np.ndarray, render_mode: str = FINAL) -> Image.Image:
        source_points = np.asarray(source_points, dtype=np.float32)
        if source_points.shape != (4, 2):
            raise ValueError("透视控制点必须是 4 个二维点。")
        source_points = self._clamp_points(source_points, image.size)
        if not self.is_valid_quad(source_points):
            raise ValueError("透视控制点构成的区域无效。")

        width, height = image.size
        destination = np.array(
            [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
            dtype=np.float32,
        )
        matrix = cv2.getPerspectiveTransform(source_points, destination)
        cv_image = pil_to_cv(image)
        interpolation = cv2.INTER_LINEAR if render_mode == self.PREVIEW else cv2.INTER_LANCZOS4
        warped = cv2.warpPerspective(
            cv_image,
            matrix,
            (width, height),
            flags=interpolation,
            borderMode=cv2.BORDER_REPLICATE,
        )
        return cv_to_pil(warped, image.mode)

    def is_valid_quad(self, points: np.ndarray) -> bool:
        if self._polygon_area(points) < 10.0:
            return False
        cross_values = []
        for index in range(4):
            a = points[index]
            b = points[(index + 1) % 4]
            c = points[(index + 2) % 4]
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            cross_values.append(cross)
        return all(value > 0 for value in cross_values) or all(value < 0 for value in cross_values)

    def _polygon_area(self, points: np.ndarray) -> float:
        x = points[:, 0]
        y = points[:, 1]
        return float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) * 0.5)

    def _clamp_points(self, points: np.ndarray, size: tuple[int, int]) -> np.ndarray:
        width, height = size
        clamped = points.copy()
        clamped[:, 0] = np.clip(clamped[:, 0], 0, max(0, width - 1))
        clamped[:, 1] = np.clip(clamped[:, 1], 0, max(0, height - 1))
        return clamped
