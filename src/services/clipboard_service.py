"""
ClipboardService – clipboard write operations.

Responsibility: abstract clipboard interaction so higher layers
don't depend on tk directly and the service is testable/replaceable.
"""

from __future__ import annotations

from typing import Optional


class ClipboardService:
    """Writes text to the system clipboard via a tk root widget."""

    def __init__(self, root) -> None:  # root: tk.Tk
        self._root = root

    def copy(self, text: str) -> bool:
        """Copy text to clipboard. Returns True on success."""
        try:
            self._root.clipboard_clear()
            self._root.clipboard_append(text)
            self._root.update()
            return True
        except Exception:  # noqa: BLE001
            return False

    def read(self) -> Optional[str]:
        """Read current clipboard content, or None on failure."""
        try:
            return self._root.clipboard_get()
        except Exception:  # noqa: BLE001
            return None
