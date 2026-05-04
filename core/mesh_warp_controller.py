from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

from utils.image_utils import cv_to_pil, pil_to_cv


@dataclass(frozen=True)
class MeshRenderProfile:
    interpolation: int
    solve_dtype: type
    sample_dtype: type
    max_query_points: int
    regularization: float


class MeshWarpController:
    PREVIEW = "preview"
    FINAL = "final"

    def build_regular_grid(self, size: tuple[int, int], rows: int, cols: int) -> np.ndarray:
        width, height = size
        x_coords = np.linspace(0, width - 1, cols + 1, dtype=np.float32)
        y_coords = np.linspace(0, height - 1, rows + 1, dtype=np.float32)
        grid_x, grid_y = np.meshgrid(x_coords, y_coords)
        return np.dstack((grid_x, grid_y)).astype(np.float32)

    def warp_mesh(
        self,
        image: Image.Image,
        source_points: np.ndarray,
        target_points: np.ndarray,
        render_mode: str = FINAL,
    ) -> Image.Image:
        if source_points.shape != target_points.shape:
            raise ValueError("网格控制点数量不一致。")
        if source_points.ndim != 3 or source_points.shape[2] != 2:
            raise ValueError("网格控制点格式无效。")

        source_points = self._clamp_points(source_points, image.size)
        target_points = self._clamp_points(target_points, image.size)

        profile = self._profile(render_mode)
        map_x, map_y = self._build_tps_inverse_map(source_points, target_points, image.size, profile)
        cv_image = pil_to_cv(image)
        warped = cv2.remap(
            cv_image,
            map_x,
            map_y,
            interpolation=profile.interpolation,
            borderMode=cv2.BORDER_REFLECT_101,
        )
        return cv_to_pil(warped, image.mode)

    def _build_tps_inverse_map(
        self,
        source_points: np.ndarray,
        target_points: np.ndarray,
        size: tuple[int, int],
        profile: MeshRenderProfile,
    ) -> tuple[np.ndarray, np.ndarray]:
        width, height = size
        source = source_points.reshape(-1, 2).astype(profile.solve_dtype)
        target = target_points.reshape(-1, 2).astype(profile.solve_dtype)
        if len(source) < 3:
            raise ValueError("控制点过少，无法进行网格变形。")

        weights_x, affine_x = self._solve_tps_system(target, source[:, 0], profile)
        weights_y, affine_y = self._solve_tps_system(target, source[:, 1], profile)

        map_x = np.empty((height, width), dtype=np.float32)
        map_y = np.empty((height, width), dtype=np.float32)
        chunk_rows = max(8, profile.max_query_points // max(1, width))
        x_coords = np.arange(width, dtype=profile.sample_dtype)
        target_sample = target.astype(profile.sample_dtype)
        weights_x = weights_x.astype(profile.sample_dtype)
        weights_y = weights_y.astype(profile.sample_dtype)
        affine_x = affine_x.astype(profile.sample_dtype)
        affine_y = affine_y.astype(profile.sample_dtype)

        for start_row in range(0, height, chunk_rows):
            end_row = min(height, start_row + chunk_rows)
            y_coords = np.arange(start_row, end_row, dtype=profile.sample_dtype)
            grid_x, grid_y = np.meshgrid(x_coords, y_coords)
            query = np.column_stack((grid_x.reshape(-1), grid_y.reshape(-1)))
            radial = self._radial_basis(self._pairwise_distances(query, target_sample))
            ones = np.ones((query.shape[0], 1), dtype=profile.sample_dtype)
            affine_terms = np.hstack((ones, query))

            mapped_x = radial @ weights_x + affine_terms @ affine_x
            mapped_y = radial @ weights_y + affine_terms @ affine_y
            block_height = end_row - start_row
            map_x[start_row:end_row] = mapped_x.reshape(block_height, width).astype(np.float32)
            map_y[start_row:end_row] = mapped_y.reshape(block_height, width).astype(np.float32)

        map_x = np.clip(map_x, 0, max(0, width - 1))
        map_y = np.clip(map_y, 0, max(0, height - 1))
        return map_x, map_y

    def _solve_tps_system(
        self,
        control_points: np.ndarray,
        values: np.ndarray,
        profile: MeshRenderProfile,
    ) -> tuple[np.ndarray, np.ndarray]:
        count = control_points.shape[0]
        pairwise = self._pairwise_distances(control_points, control_points)
        kernel = self._radial_basis(pairwise)
        kernel += np.eye(count, dtype=profile.solve_dtype) * profile.regularization

        p_matrix = np.hstack((np.ones((count, 1), dtype=profile.solve_dtype), control_points))
        system = np.zeros((count + 3, count + 3), dtype=profile.solve_dtype)
        system[:count, :count] = kernel
        system[:count, count:] = p_matrix
        system[count:, :count] = p_matrix.T

        rhs = np.zeros(count + 3, dtype=profile.solve_dtype)
        rhs[:count] = values

        solution = np.linalg.solve(system, rhs)
        return solution[:count], solution[count:]

    def _pairwise_distances(self, points_a: np.ndarray, points_b: np.ndarray) -> np.ndarray:
        delta = points_a[:, None, :] - points_b[None, :, :]
        return np.sqrt(np.sum(delta * delta, axis=2))

    def _radial_basis(self, radius: np.ndarray) -> np.ndarray:
        squared = radius * radius
        safe_squared = np.where(squared > 0, squared, 1.0)
        return squared * np.log(safe_squared)

    def _profile(self, render_mode: str) -> MeshRenderProfile:
        if render_mode == self.PREVIEW:
            return MeshRenderProfile(
                interpolation=cv2.INTER_LINEAR,
                solve_dtype=np.float64,
                sample_dtype=np.float32,
                max_query_points=120_000,
                regularization=2e-3,
            )
        return MeshRenderProfile(
            interpolation=cv2.INTER_LANCZOS4,
            solve_dtype=np.float64,
            sample_dtype=np.float64,
            max_query_points=420_000,
            regularization=5e-4,
        )

    def _clamp_points(self, points: np.ndarray, size: tuple[int, int]) -> np.ndarray:
        width, height = size
        clamped = points.copy()
        clamped[..., 0] = np.clip(clamped[..., 0], 0, max(0, width - 1))
        clamped[..., 1] = np.clip(clamped[..., 1], 0, max(0, height - 1))
        return clamped
