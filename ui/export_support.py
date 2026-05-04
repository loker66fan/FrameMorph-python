from __future__ import annotations

import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from PIL import Image
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QFrame

from utils.image_utils import ExportCancelledError, save_image_file


SUPERRES_MODEL_CACHE_DIR = Path(__file__).resolve().parent.parent / "models" / "opencv_dnn_superres"


DNN_SUPERRES_MODEL_SPECS = {
    "edsr": {
        "label": "EDSR",
        "scales": [2, 3, 4],
        "download_url": "https://github.com/Saafke/EDSR_Tensorflow/tree/master/models",
        "download_raw_base": "https://raw.githubusercontent.com/Saafke/EDSR_Tensorflow/master/models",
        "code_url": "https://github.com/Saafke/EDSR_Tensorflow",
        "paper_url": "https://arxiv.org/abs/1707.02921",
        "summary": "高精度，较慢，文件较大。",
        "details": "x2 / x3 / x4，约 38.5MB 量化版，适合追求画质的场景。",
    },
    "espcn": {
        "label": "ESPCN",
        "scales": [2, 3, 4],
        "download_url": "https://github.com/fannymonori/TF-ESPCN/tree/master/export",
        "download_raw_base": "https://raw.githubusercontent.com/fannymonori/TF-ESPCN/master/export",
        "code_url": "https://github.com/fannymonori/TF-ESPCN",
        "paper_url": "https://arxiv.org/abs/1609.05158",
        "summary": "体积很小，速度很快。",
        "details": "x2 / x3 / x4，约 100KB，适合轻量和实时预览。",
    },
    "fsrcnn": {
        "label": "FSRCNN",
        "scales": [2, 3, 4],
        "download_url": "https://github.com/Saafke/FSRCNN_Tensorflow/tree/master/models",
        "download_raw_base": "https://raw.githubusercontent.com/Saafke/FSRCNN_Tensorflow/master/models",
        "code_url": "https://github.com/Saafke/FSRCNN_Tensorflow",
        "paper_url": "https://arxiv.org/abs/1608.00367",
        "summary": "速度快、模型小、精度均衡。",
        "details": "x2 / x3 / x4，也支持识别 FSRCNN-small 文件名。",
    },
    "lapsrn": {
        "label": "LapSRN",
        "scales": [2, 4, 8],
        "download_url": "https://github.com/fannymonori/TF-LapSRN/tree/master/export",
        "download_raw_base": "https://raw.githubusercontent.com/fannymonori/TF-LapSRN/master/export",
        "code_url": "https://github.com/fannymonori/TF-LapSRN",
        "paper_url": "https://arxiv.org/abs/1710.01992",
        "summary": "支持多倍率，速度与画质居中。",
        "details": "x2 / x4 / x8，约 1-5MB，适合多尺度放大。",
    },
}


class ModelDownloadThread(QThread):
    progress_changed = Signal(str)
    download_finished = Signal(str)
    download_failed = Signal(str)

    def __init__(self, url: str, destination: Path, parent: Optional[QFrame] = None) -> None:
        super().__init__(parent)
        self.url = url
        self.destination = destination

    def run(self) -> None:
        try:
            self.destination.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self.destination.with_suffix(self.destination.suffix + ".part")
            request = urllib.request.Request(self.url, headers={"User-Agent": "jianji-superres-downloader"})
            with urllib.request.urlopen(request, timeout=60) as response, temp_path.open("wb") as file:
                total = response.headers.get("Content-Length")
                total_bytes = int(total) if total and total.isdigit() else 0
                received = 0
                while True:
                    chunk = response.read(1024 * 128)
                    if not chunk:
                        break
                    file.write(chunk)
                    received += len(chunk)
                    if total_bytes > 0:
                        progress = received / total_bytes * 100.0
                        self.progress_changed.emit(f"正在下载：{self.destination.name}  {progress:.1f}%")
                    else:
                        self.progress_changed.emit(f"正在下载：{self.destination.name}  {received // 1024} KB")
            temp_path.replace(self.destination)
        except urllib.error.HTTPError as exc:
            self.download_failed.emit(f"下载失败：HTTP {exc.code} {self.destination.name}")
            return
        except urllib.error.URLError as exc:
            self.download_failed.emit(f"下载失败：{exc.reason}")
            return
        except Exception as exc:
            self.download_failed.emit(f"下载失败：{exc}")
            return
        self.download_finished.emit(str(self.destination))


class ExportImageThread(QThread):
    progress_changed = Signal(int, str, str)
    export_finished = Signal(str)
    export_failed = Signal(str)
    export_cancelled = Signal(str)

    def __init__(
        self,
        image: Image.Image,
        path: str,
        quality: int,
        parent: Optional[QFrame] = None,
    ) -> None:
        super().__init__(parent)
        self.image = image.copy()
        self.path = path
        self.quality = quality
        self._cancel_requested = False
        self._start_time = 0.0

    def cancel(self) -> None:
        self._cancel_requested = True

    def _is_cancelled(self) -> bool:
        return self._cancel_requested

    def _emit_progress(self, percent: float, stage: str) -> None:
        percent = max(0, min(100, int(round(percent * 100))))
        elapsed = max(0.001, time.monotonic() - self._start_time)
        if percent <= 0:
            eta = "预计剩余时间：计算中"
        else:
            total_estimated = elapsed / max(percent / 100.0, 0.01)
            remaining = max(0.0, total_estimated - elapsed)
            eta = f"预计剩余时间：{self._format_seconds(remaining)}"
        self.progress_changed.emit(percent, stage, eta)

    @staticmethod
    def _format_seconds(seconds: float) -> str:
        if seconds < 60:
            return f"{int(round(seconds))} 秒"
        minutes, secs = divmod(int(round(seconds)), 60)
        if minutes < 60:
            return f"{minutes} 分 {secs} 秒"
        hours, minutes = divmod(minutes, 60)
        return f"{hours} 小时 {minutes} 分"

    def run(self) -> None:
        self._start_time = time.monotonic()
        try:
            self._emit_progress(0.02, "准备导出…")
            save_image_file(
                self.image,
                self.path,
                quality=self.quality,
                progress_callback=self._emit_progress,
                is_cancelled=self._is_cancelled,
            )
        except ExportCancelledError as exc:
            self.export_cancelled.emit(str(exc))
            return
        except Exception as exc:
            self.export_failed.emit(str(exc))
            return
        self.progress_changed.emit(100, "导出完成", "预计剩余时间：0 秒")
        self.export_finished.emit(self.path)
