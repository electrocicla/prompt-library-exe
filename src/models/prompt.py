"""
Prompt – core domain model.

Responsibility: define and validate a single prompt entry.
No persistence, no UI, no business logic beyond validation.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum


class PromptRole(str, Enum):
    """Role that a prompt plays during composition."""
    BODY = "body"
    PREFIX = "prefix"
    SUFFIX = "suffix"


@dataclass
class Prompt:
    """Immutable-ish prompt entry with identity, metadata and content."""

    id: str
    name: str
    content: str
    role: PromptRole
    category: str
    usage_count: int
    is_favorite: bool
    created_at: float
    updated_at: float

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @staticmethod
    def create(name: str, content: str, role: PromptRole, category: str) -> "Prompt":
        now = time.time()
        return Prompt(
            id=str(uuid.uuid4()),
            name=name.strip(),
            content=content,
            role=role,
            category=category.strip() or "general",
            usage_count=0,
            is_favorite=False,
            created_at=now,
            updated_at=now,
        )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "content": self.content,
            "role": self.role.value,
            "category": self.category,
            "usage_count": self.usage_count,
            "is_favorite": self.is_favorite,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "Prompt":
        role_raw = data.get("role", "body")
        try:
            role = PromptRole(role_raw)
        except ValueError:
            role = PromptRole.BODY

        return Prompt(
            id=str(data.get("id", str(uuid.uuid4()))),
            name=str(data.get("name", "Unnamed")),
            content=str(data.get("content", "")),
            role=role,
            category=str(data.get("category", "general")),
            usage_count=int(data.get("usage_count", 0)),
            is_favorite=bool(data.get("is_favorite", False)),
            created_at=float(data.get("created_at", time.time())),
            updated_at=float(data.get("updated_at", time.time())),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def with_updated_fields(self, **kwargs) -> "Prompt":
        """Return a new Prompt with given fields overwritten."""
        data = self.to_dict()
        data.update(kwargs)
        data["updated_at"] = time.time()
        return Prompt.from_dict(data)

    @property
    def rank_score(self) -> float:
        """Higher is better. Favorites get a 10 000 bonus."""
        favourite_bonus = 10_000 if self.is_favorite else 0
        return self.usage_count + favourite_bonus
