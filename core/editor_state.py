from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from core.text_controller import TextOverlay


@dataclass
class EditorState:
    image: Image.Image
    text_items: list[TextOverlay]
