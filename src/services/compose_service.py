"""
ComposeService – text composition logic.

Responsibility: assemble a final prompt text from ordered prefix
entries, a body string, and ordered suffix entries. No UI, no I/O.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Sequence

from models.prompt import Prompt


class ComposeSeparator(str, Enum):
    """How individual parts are joined during composition."""
    NEWLINE = "newline"
    SPACE = "space"
    DOUBLE_NEWLINE = "double_newline"
    CUSTOM = "custom"

    def label(self) -> str:
        labels = {
            self.NEWLINE: "New Line (\\n)",
            self.SPACE: "Space",
            self.DOUBLE_NEWLINE: "Blank Line (\\n\\n)",
            self.CUSTOM: "Custom",
        }
        return labels[self]

    def to_str(self, custom: str = " ") -> str:
        mapping = {
            self.NEWLINE: "\n",
            self.SPACE: " ",
            self.DOUBLE_NEWLINE: "\n\n",
            self.CUSTOM: custom,
        }
        return mapping[self]


class ComposeService:
    """Assembles composed prompts from parts."""

    def compose(
        self,
        prefixes: Sequence[Prompt],
        body: str,
        suffixes: Sequence[Prompt],
        separator: ComposeSeparator = ComposeSeparator.NEWLINE,
        custom_separator: str = " ",
    ) -> str:
        """
        Join prefixes → body → suffixes with the chosen separator.

        Each of prefixes and suffixes may contain multiple prompts;
        they are joined with the same separator as the main parts.
        """
        sep = separator.to_str(custom_separator)
        parts: List[str] = []

        for p in prefixes:
            if p.content.strip():
                parts.append(p.content)

        if body.strip():
            parts.append(body)

        for s in suffixes:
            if s.content.strip():
                parts.append(s.content)

        return sep.join(parts)

    def preview(
        self,
        prefixes: Sequence[Prompt],
        body: str,
        suffixes: Sequence[Prompt],
        separator: ComposeSeparator = ComposeSeparator.NEWLINE,
        custom_separator: str = " ",
        max_chars: int = 300,
    ) -> str:
        """Return truncated preview for display in UI."""
        full = self.compose(prefixes, body, suffixes, separator, custom_separator)
        if len(full) <= max_chars:
            return full
        return full[:max_chars] + "…"
