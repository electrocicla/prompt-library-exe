"""
PromptService – CRUD operations on the prompt collection.

Responsibility: manage prompt lifecycle (create, read, update, delete,
favourite, increment usage). Delegates persistence to StorageService.
Single source of truth for the in-memory state.
"""

from __future__ import annotations

import time
from typing import Callable, List, Optional

from models.prompt import Prompt, PromptRole
from models.library_state import LibraryState
from services.storage_service import StorageService


# Observers notify UI of state changes without coupling to tkinter/CTk.
StateChangedCallback = Callable[[LibraryState], None]


class PromptService:
    """Manages all prompt CRUD and persistence coordination."""

    def __init__(self, storage: StorageService) -> None:
        self._storage = storage
        self._state: LibraryState = storage.load()
        self._observers: List[StateChangedCallback] = []

    # ------------------------------------------------------------------
    # Observer pattern (decouples service from UI layer)
    # ------------------------------------------------------------------

    def subscribe(self, callback: StateChangedCallback) -> None:
        """Register a callback that fires on every state mutation."""
        self._observers.append(callback)

    def unsubscribe(self, callback: StateChangedCallback) -> None:
        self._observers = [cb for cb in self._observers if cb is not callback]

    def _notify(self) -> None:
        for cb in self._observers:
            cb(self._state)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @property
    def state(self) -> LibraryState:
        return self._state

    def get_all(self) -> List[Prompt]:
        return list(self._state.prompts)

    def get_by_role(self, role: PromptRole) -> List[Prompt]:
        return [p for p in self._state.prompts if p.role == role]

    def search(self, query: str) -> List[Prompt]:
        if not query:
            return self.get_all()
        q = query.lower()
        return [
            p for p in self._state.prompts
            if q in p.name.lower() or q in p.content.lower() or q in p.category.lower()
        ]

    def ranked(self, prompts: Optional[List[Prompt]] = None) -> List[Prompt]:
        """Return prompts sorted by rank_score descending."""
        src = prompts if prompts is not None else self.get_all()
        return sorted(src, key=lambda p: p.rank_score, reverse=True)

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def create(self, name: str, content: str, role: PromptRole, category: str) -> Prompt:
        prompt = Prompt.create(name, content, role, category)
        self._state.prompts.append(prompt)
        self._persist()
        return prompt

    def update(self, prompt_id: str, **kwargs) -> Optional[Prompt]:
        for i, p in enumerate(self._state.prompts):
            if p.id == prompt_id:
                updated = p.with_updated_fields(**kwargs)
                self._state.prompts[i] = updated
                self._persist()
                return updated
        return None

    def delete(self, prompt_id: str) -> bool:
        before = len(self._state.prompts)
        self._state.prompts = [p for p in self._state.prompts if p.id != prompt_id]
        changed = len(self._state.prompts) < before
        if changed:
            self._persist()
        return changed

    def toggle_favorite(self, prompt_id: str) -> Optional[Prompt]:
        for p in self._state.prompts:
            if p.id == prompt_id:
                return self.update(prompt_id, is_favorite=not p.is_favorite)
        return None

    def increment_usage(self, prompt_id: str) -> None:
        for p in self._state.prompts:
            if p.id == prompt_id:
                self.update(prompt_id, usage_count=p.usage_count + 1)
                return

    def import_state(self, new_state: LibraryState, merge: bool = False) -> None:
        """Replace or merge imported prompts. Deduplicates by ID."""
        if merge:
            existing_ids = {p.id for p in self._state.prompts}
            for p in new_state.prompts:
                if p.id not in existing_ids:
                    self._state.prompts.append(p)
        else:
            self._state = new_state
        self._persist()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _persist(self) -> None:
        self._storage.save(self._state)
        self._notify()
