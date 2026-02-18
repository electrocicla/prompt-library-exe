"""
LibraryState – snapshot of all mutable library data.

Responsibility: act as a plain data container for the full state
that the StorageService persists and the PromptService operates on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .prompt import Prompt


SCHEMA_VERSION = 1


@dataclass
class LibraryState:
    """Full serialisable state of the prompt library."""

    schema_version: int
    prompts: List[Prompt] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @staticmethod
    def empty() -> "LibraryState":
        return LibraryState(schema_version=SCHEMA_VERSION, prompts=[])

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "prompts": [p.to_dict() for p in self.prompts],
        }

    @staticmethod
    def from_dict(data: dict[str, object]) -> "LibraryState":
        prompts_raw = data.get("prompts", [])
        prompts = [Prompt.from_dict(p) for p in prompts_raw if isinstance(p, dict)]
        return LibraryState(
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
            prompts=prompts,
        )
