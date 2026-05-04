from __future__ import annotations

from typing import Optional

import numpy as np
from PIL import Image
from PySide6.QtCore import QThread, Signal

from core.mesh_warp_controller import MeshWarpController
from core.perspective_controller import PerspectiveController
from utils.image_utils import scaled_preview_image


class LiveWarpPreviewThread(QThread):
    preview_ready = Signal(int, object, object)
    preview_failed = Signal(int, str)

    def __init__(
        self,
        image: Image.Image,
        mode: str,
        generation: int,
        preview_max_side: int,
        source_points: Optional[np.ndarray] = None,
        target_points: Optional[np.ndarray] = None,
        perspective_points: Optional[np.ndarray] = None,
    ) -> None:
        super().__init__()
        self.image = image.copy()
        self.mode = mode
        self.generation = generation
        self.preview_max_side = preview_max_side
        self.source_points = None if source_points is None else source_points.copy()
        self.target_points = None if target_points is None else target_points.copy()
        self.perspective_points = None if perspective_points is None else perspective_points.copy()

    def run(self) -> None:
        try:
            preview_input, scale = scaled_preview_image(self.image, self.preview_max_side)
            if self.mode == "mesh":
                if self.source_points is None or self.target_points is None:
                    raise ValueError("缺少网格控制点。")
                controller = MeshWarpController()
                preview_image = controller.warp_mesh(
                    preview_input,
                    self.source_points * scale,
                    self.target_points * scale,
                    render_mode=controller.PREVIEW,
                )
            elif self.mode == "perspective":
                if self.perspective_points is None:
                    raise ValueError("缺少透视控制点。")
                controller = PerspectiveController()
                preview_image = controller.warp(
                    preview_input,
                    self.perspective_points * scale,
                    render_mode=controller.PREVIEW,
                )
            else:
                raise ValueError(f"不支持的预览模式：{self.mode}")
        except Exception as exc:
            self.preview_failed.emit(self.generation, str(exc))
            return

        self.preview_ready.emit(self.generation, preview_image, self.image.size)


class MeshWarpApplyThread(QThread):
    warp_finished = Signal(object)
    warp_failed = Signal(str)

    def __init__(
        self,
        image: Image.Image,
        source_points: np.ndarray,
        target_points: np.ndarray,
    ) -> None:
        super().__init__()
        self.image = image.copy()
        self.source_points = source_points.copy()
        self.target_points = target_points.copy()

    def run(self) -> None:
        try:
            controller = MeshWarpController()
            result = controller.warp_mesh(
                self.image,
                self.source_points,
                self.target_points,
                render_mode=controller.FINAL,
            )
        except Exception as exc:
            self.warp_failed.emit(str(exc))
            return

        self.warp_finished.emit(result)
