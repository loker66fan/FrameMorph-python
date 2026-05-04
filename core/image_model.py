from pathlib import Path
from typing import Optional

from PIL import Image

from core.text_controller import TextOverlay
from utils.image_utils import open_image_file


class ImageModel:
    def __init__(self) -> None:
        self.path: Optional[Path] = None
        self.original_image: Optional[Image.Image] = None
        self.current_image: Optional[Image.Image] = None
        self.preview_image: Optional[Image.Image] = None
        self.text_items: list[TextOverlay] = []

    @property
    def has_image(self) -> bool:
        return self.current_image is not None

    @property
    def display_image(self) -> Optional[Image.Image]:
        return self.preview_image or self.current_image

    def load(self, path: str) -> Image.Image:
        image = open_image_file(path)
        self.path = Path(path)
        self.original_image = image.copy()
        self.current_image = image.copy()
        self.preview_image = None
        self.text_items = []
        return self.current_image

    def set_current_image(self, image: Image.Image) -> None:
        self.current_image = image.copy()
        self.preview_image = None

    def set_preview_image(self, image: Image.Image) -> None:
        self.preview_image = image.copy()

    def clear_preview(self) -> None:
        self.preview_image = None

    def set_text_items(self, items: list[TextOverlay]) -> None:
        self.text_items = [item.copy() for item in items]
