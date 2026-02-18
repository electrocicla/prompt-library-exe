"""
StorageService – JSON file persistence.

Responsibility: read/write LibraryState to a JSON file.
Knows nothing about UI or business logic.
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import time
from typing import Optional

from models.library_state import LibraryState


def _default_data_dir() -> pathlib.Path:
    """Return platform-appropriate application data directory."""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return pathlib.Path(base) / "NotMetaPromptLibrary"


class StorageService:
    """Handles loading and saving LibraryState to disk."""

    def __init__(self, data_dir: Optional[pathlib.Path] = None) -> None:
        self._dir = data_dir or _default_data_dir()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / "prompts.json"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> LibraryState:
        """Load state from disk. Returns empty state on any error."""
        if not self._path.exists():
            return LibraryState.empty()

        try:
            raw = self._path.read_text(encoding="utf-8")
            data: dict[str, object] = json.loads(raw)
            return LibraryState.from_dict(data)
        except Exception:  # noqa: BLE001 – intentional catch-all for corrupted data
            return LibraryState.empty()

    def save(self, state: LibraryState) -> None:
        """Persist state to disk atomically (write-and-rename)."""
        tmp = self._path.with_suffix(".tmp")
        try:
            tmp.write_text(
                json.dumps(state.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            shutil.move(str(tmp), str(self._path))
        except Exception as exc:  # noqa: BLE001
            print(f"[StorageService] Save failed: {exc}")
            if tmp.exists():
                tmp.unlink(missing_ok=True)

    def export_json(self, state: LibraryState) -> str:
        """Return pretty-printed JSON of the full state."""
        return json.dumps(state.to_dict(), indent=2, ensure_ascii=False)

    def import_json(self, raw_json: str) -> LibraryState:
        """Parse and return a LibraryState from a JSON string."""
        data: dict[str, object] = json.loads(raw_json)
        return LibraryState.from_dict(data)

    @property
    def storage_path(self) -> pathlib.Path:
        return self._path
