from collections import deque
from typing import Optional

from PIL import Image

from core.editor_state import EditorState
from core.text_controller import TextOverlay, TextOverlayController


class HistoryManager:
    def __init__(self, max_states: int = 20) -> None:
        self.max_states = max_states
        self._undo_stack: deque[EditorState] = deque(maxlen=max_states)
        self._redo_stack: list[EditorState] = []
        self._text_controller = TextOverlayController()

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 1

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def clear_with(self, image: Image.Image, text_items: Optional[list[TextOverlay]] = None) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._undo_stack.append(self._snapshot(image, text_items or []))

    def record(self, image: Image.Image, text_items: Optional[list[TextOverlay]] = None) -> None:
        self._undo_stack.append(self._snapshot(image, text_items or []))
        self._redo_stack.clear()

    def undo(self) -> Optional[EditorState]:
        if not self.can_undo:
            return None
        current = self._undo_stack.pop()
        self._redo_stack.append(self._snapshot(current.image, current.text_items))
        previous = self._undo_stack[-1]
        return self._snapshot(previous.image, previous.text_items)

    def redo(self) -> Optional[EditorState]:
        if not self.can_redo:
            return None
        image = self._redo_stack.pop()
        self._undo_stack.append(self._snapshot(image.image, image.text_items))
        return self._snapshot(image.image, image.text_items)

    def _snapshot(self, image: Image.Image, text_items: list[TextOverlay]) -> EditorState:
        return EditorState(image=image.copy(), text_items=self._text_controller.clone_items(text_items))
