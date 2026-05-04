from __future__ import annotations

import io
from pathlib import Path
from typing import Callable, Optional

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


class ExportCancelledError(RuntimeError):
    """Raised when a long-running export operation is cancelled."""


def open_image_file(path: str) -> Image.Image:
    with Image.open(path) as image:
        normalized = ImageOps.exif_transpose(image)
        if normalized.mode not in {"RGB", "RGBA"}:
            normalized = normalized.convert("RGBA")
        return normalized.copy()


def pil_to_qpixmap(image: Image.Image) -> QPixmap:
    from PySide6.QtGui import QPixmap

    return QPixmap.fromImage(pil_to_qimage(image))


def pil_to_qimage(image: Image.Image) -> QImage:
    from PySide6.QtGui import QImage

    if image.mode not in {"RGB", "RGBA"}:
        image = image.convert("RGBA")

    if image.mode == "RGBA":
        raw = image.tobytes("raw", "RGBA")
        qimage = QImage(raw, image.width, image.height, image.width * 4, QImage.Format.Format_RGBA8888)
    else:
        raw = image.tobytes("raw", "RGB")
        qimage = QImage(raw, image.width, image.height, image.width * 3, QImage.Format.Format_RGB888)
    return qimage.copy()


def qimage_to_pil(image: QImage, target_mode: str = "RGBA") -> Image.Image:
    from PySide6.QtGui import QImage

    converted = image.convertToFormat(QImage.Format.Format_RGBA8888)
    width = converted.width()
    height = converted.height()
    bits = converted.bits()
    array = np.frombuffer(bits, dtype=np.uint8).reshape((height, width, 4))
    pil_image = Image.fromarray(array.copy(), mode="RGBA")
    if target_mode in {"RGB", "RGBA", "L"}:
        return pil_image.convert(target_mode)
    return pil_image


def pil_to_cv(image: Image.Image) -> np.ndarray:
    if image.mode == "RGBA":
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGBA2BGRA)
    if image.mode == "RGB":
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    if image.mode == "L":
        return np.array(image)
    return pil_to_cv(image.convert("RGBA"))


def cv_to_pil(image: np.ndarray, target_mode: str = "RGB") -> Image.Image:
    if image.ndim == 2:
        pil_image = Image.fromarray(image, mode="L")
    elif image.shape[2] == 4:
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA), mode="RGBA")
    else:
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), mode="RGB")
    if target_mode in {"RGB", "RGBA", "L"}:
        return pil_image.convert(target_mode)
    return pil_image


def scaled_preview_image(image: Image.Image, max_side: int = 720) -> tuple[Image.Image, float]:
    width, height = image.size
    longest_side = max(width, height)
    if longest_side <= max_side:
        return image.copy(), 1.0

    scale = max_side / longest_side
    preview_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return image.resize(preview_size, Image.BICUBIC), scale


def _resize_alpha_channel(alpha: Optional[Image.Image], size: tuple[int, int]) -> Optional[Image.Image]:
    if alpha is None:
        return None
    return alpha.resize(size, Image.LANCZOS)


def infer_dnn_model_metadata(model_path: str) -> tuple[Optional[str], Optional[int]]:
    filename = Path(model_path).name.lower()
    inferred_model = None
    for model_name in ("edsr", "espcn", "fsrcnn", "lapsrn"):
        if model_name in filename:
            inferred_model = model_name
            break
    inferred_scale = None
    for part in filename.replace(".", "_").split("_"):
        if part.startswith("x") and part[1:].isdigit():
            inferred_scale = int(part[1:])
            break
    return inferred_model, inferred_scale


def save_image_file(
    image: Image.Image,
    path: str,
    quality: int = 95,
    progress_callback: Optional[Callable[[float, str], None]] = None,
    is_cancelled: Optional[Callable[[], bool]] = None,
) -> None:
    suffix = Path(path).suffix.lower()
    quality = max(1, min(100, quality))
    if progress_callback is not None:
        progress_callback(0.05, "正在编码图片…")
    if is_cancelled is not None and is_cancelled():
        raise ExportCancelledError("导出已取消。")

    buffer = io.BytesIO()
    if suffix in {".jpg", ".jpeg"}:
        subsampling = 0 if quality >= 97 else 1 if quality >= 92 else 2
        image.convert("RGB").save(
            buffer,
            format="JPEG",
            quality=min(quality, 95),
            optimize=True,
            progressive=True,
            subsampling=subsampling,
        )
    elif suffix == ".png":
        compress_level = int(round((100 - quality) / 100 * 9))
        image.save(
            buffer,
            format="PNG",
            optimize=True,
            compress_level=max(0, min(9, compress_level)),
        )
    else:
        image.save(buffer, format=Image.registered_extensions().get(suffix, suffix.replace(".", "").upper()) or None)

    if is_cancelled is not None and is_cancelled():
        raise ExportCancelledError("导出已取消。")

    if progress_callback is not None:
        progress_callback(0.45, "正在写入磁盘…")

    data = buffer.getvalue()
    total_bytes = max(1, len(data))
    temp_path = Path(path).with_suffix(Path(path).suffix + ".part")
    try:
        with temp_path.open("wb") as file:
            chunk_size = 1024 * 256
            written = 0
            for offset in range(0, total_bytes, chunk_size):
                if is_cancelled is not None and is_cancelled():
                    raise ExportCancelledError("导出已取消。")
                chunk = data[offset : offset + chunk_size]
                file.write(chunk)
                written += len(chunk)
                if progress_callback is not None:
                    progress = 0.45 + written / total_bytes * 0.55
                    progress_callback(min(1.0, progress), "正在写入磁盘…")
        temp_path.replace(path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise


def resolve_export_path(path: str, selected_filter: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg"}:
        return path
    if "PNG" in selected_filter.upper():
        return f"{path}.png"
    if "JPG" in selected_filter.upper() or "JPEG" in selected_filter.upper():
        return f"{path}.jpg"
    return f"{path}.png"


def enhance_image_for_export(
    image: Image.Image,
    scale_factor: float = 2.0,
    sharpen_strength: float = 1.25,
) -> Image.Image:
    scale_factor = max(1.0, float(scale_factor))
    width = max(1, round(image.width * scale_factor))
    height = max(1, round(image.height * scale_factor))
    alpha = image.getchannel("A") if "A" in image.getbands() else None
    enhanced = image.convert("RGB").resize((width, height), Image.LANCZOS) if scale_factor > 1.0 else image.convert("RGB")

    # Only sharpen the luminance channel so enlarged exports keep their original colors.
    y_channel, cb_channel, cr_channel = enhanced.convert("YCbCr").split()
    sharpened_luma = ImageEnhance.Sharpness(y_channel).enhance(1.0 + max(0.0, sharpen_strength - 1.0) * 0.35)
    sharpen_percent = int(round(120 + max(0.0, sharpen_strength - 1.0) * 80))
    sharpened_luma = sharpened_luma.filter(
        ImageFilter.UnsharpMask(radius=1.6, percent=max(80, min(240, sharpen_percent)), threshold=2)
    )
    result = Image.merge("YCbCr", (sharpened_luma, cb_channel, cr_channel)).convert("RGB")
    resized_alpha = _resize_alpha_channel(alpha, result.size)
    if resized_alpha is not None:
        result.putalpha(resized_alpha)
    return result


def enhance_image_super_resolution(
    image: Image.Image,
    scale_factor: float = 2.0,
    sharpen_strength: float = 1.2,
) -> Image.Image:
    return enhance_image_for_export(image, scale_factor=scale_factor, sharpen_strength=sharpen_strength)


def enhance_image_srcnn(
    image: Image.Image,
    scale_factor: float = 2.0,
    model_path: Optional[str] = None,
) -> Image.Image:
    try:
        import torch
        import torch.nn as nn
    except Exception as exc:  # pragma: no cover - runtime env dependent
        raise RuntimeError("未安装 PyTorch，无法使用 SRCNN 增强。") from exc

    class SRCNN(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.patch_extraction = nn.Conv2d(1, 64, kernel_size=9, padding=4)
            self.non_linear_mapping = nn.Conv2d(64, 32, kernel_size=5, padding=2)
            self.reconstruction = nn.Conv2d(32, 1, kernel_size=5, padding=2)
            self.relu = nn.ReLU(inplace=True)

        def forward(self, x):
            x = self.relu(self.patch_extraction(x))
            x = self.relu(self.non_linear_mapping(x))
            return self.reconstruction(x)

    if not model_path or not Path(model_path).exists():
        raise RuntimeError("SRCNN 模型文件缺失，请配置有效的 `.pth` 模型路径。")

    scale_factor = max(1.0, float(scale_factor))
    target_size = (
        max(1, round(image.width * scale_factor)),
        max(1, round(image.height * scale_factor)),
    )
    alpha = image.getchannel("A") if "A" in image.getbands() else None
    upscaled = image.convert("RGB").resize(target_size, Image.BICUBIC).convert("YCbCr")
    y, cb, cr = upscaled.split()
    y_array = np.asarray(y, dtype=np.float32) / 255.0
    y_tensor = torch.from_numpy(y_array).unsqueeze(0).unsqueeze(0)

    model = SRCNN()
    checkpoint = torch.load(model_path, map_location="cpu")
    state_dict = checkpoint.get("state_dict", checkpoint)
    cleaned_state_dict = {}
    for key, value in state_dict.items():
        cleaned_state_dict[key.replace("module.", "")] = value
    model.load_state_dict(cleaned_state_dict, strict=False)
    model.eval()

    with torch.no_grad():
        output = model(y_tensor).clamp_(0.0, 1.0)
    output_image = Image.fromarray((output.squeeze().numpy() * 255.0).astype(np.uint8), mode="L")
    merged = Image.merge("YCbCr", (output_image, cb, cr)).convert("RGB")
    resized_alpha = _resize_alpha_channel(alpha, merged.size)
    if resized_alpha is not None:
        merged.putalpha(resized_alpha)
    return merged


def enhance_image_dnn_superres(
    image: Image.Image,
    model_name: str,
    scale: int,
    model_path: Optional[str],
) -> Image.Image:
    if not hasattr(cv2, "dnn_superres"):
        raise RuntimeError("当前 OpenCV 未包含 dnn_superres，请安装 opencv-contrib-python。")
    if not model_path or not Path(model_path).exists():
        raise RuntimeError("未找到 dnn_superres 模型文件，请配置有效的模型路径。")

    model_name = model_name.lower().strip()
    scale = int(scale)
    inferred_model, inferred_scale = infer_dnn_model_metadata(model_path)
    if inferred_model is not None and inferred_model != model_name:
        raise RuntimeError(
            f"模型文件与当前选择不匹配：文件 `{Path(model_path).name}` 看起来是 `{inferred_model}`，当前选择是 `{model_name}`。"
        )
    if inferred_scale is not None and inferred_scale != scale:
        raise RuntimeError(
            f"模型文件与当前倍率不匹配：文件 `{Path(model_path).name}` 看起来是 `x{inferred_scale}`，当前选择是 `x{scale}`。"
        )

    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    sr.readModel(model_path)
    sr.setModel(model_name, scale)
    alpha = image.getchannel("A") if "A" in image.getbands() else None
    cv_image = pil_to_cv(image.convert("RGB"))
    try:
        result = sr.upsample(cv_image)
    except cv2.error as exc:
        raise RuntimeError(
            f"OpenCV 超分失败，请检查模型类型、倍率与文件是否一致。当前：{model_name} x{scale}；文件：{Path(model_path).name}"
        ) from exc
    pil_image = cv_to_pil(result, "RGB")
    resized_alpha = _resize_alpha_channel(alpha, pil_image.size)
    if resized_alpha is not None:
        pil_image.putalpha(resized_alpha)
    return pil_image
