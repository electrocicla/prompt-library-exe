"""
PromptCard – single prompt entry widget.

Responsibility: render one prompt with its metadata and action buttons.
Fires callbacks for copy, delete, edit, toggle-favourite; does NOT
know how to persist or compose – those are service concerns.
"""

from __future__ import annotations

from typing import Callable, Optional
import customtkinter as ctk

from models.prompt import Prompt, PromptRole
from ui.app_theme import AppTheme

# Callback type aliases for clarity
OnCopy = Callable[[Prompt], None]
OnDelete = Callable[[str], None]
OnEdit = Callable[[Prompt], None]
OnFavourite = Callable[[str], None]
OnRoleChange = Callable[[str, PromptRole], None]


class PromptCard(ctk.CTkFrame):
    """One prompt card shown in the library list."""

    def __init__(
        self,
        master,
        prompt: Prompt,
        on_copy: OnCopy,
        on_delete: OnDelete,
        on_edit: OnEdit,
        on_favourite: OnFavourite,
        on_role_change: OnRoleChange,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=AppTheme.BG_CARD,
            corner_radius=AppTheme.CARD_CORNER,
            border_width=1,
            border_color=AppTheme.BORDER,
            **kwargs,
        )
        self._prompt = prompt
        self._on_copy = on_copy
        self._on_delete = on_delete
        self._on_edit = on_edit
        self._on_favourite = on_favourite
        self._on_role_change = on_role_change

        self._build()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        p = self._prompt
        role_bg, role_fg = AppTheme.role_badge(p.role.value)

        # --- Header row ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=AppTheme.CARD_PAD, pady=(AppTheme.CARD_PAD, 4))
        header.columnconfigure(1, weight=1)

        # Favourite star
        star_text = "★" if p.is_favorite else "☆"
        star_color = AppTheme.FG_GOLD if p.is_favorite else AppTheme.FG_MUTED
        self._star_btn = ctk.CTkButton(
            header, text=star_text, width=24, height=24,
            fg_color="transparent", text_color=star_color, hover_color=AppTheme.BG_HOVER,
            font=(AppTheme.FONT_FAMILY, 14),
            command=self._handle_favourite,
        )
        self._star_btn.grid(row=0, column=0, padx=(0, 6))

        # Name label
        name_lbl = ctk.CTkLabel(
            header,
            text=p.name,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_MD, "bold"),
            text_color=AppTheme.FG_MAIN,
            anchor="w",
        )
        name_lbl.grid(row=0, column=1, sticky="ew")

        # Usage count badge
        count_lbl = ctk.CTkLabel(
            header,
            text=f"×{p.usage_count}",
            font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_XS),
            text_color=AppTheme.FG_MUTED,
        )
        count_lbl.grid(row=0, column=2, padx=(6, 0))

        # --- Category + role row ---
        meta = ctk.CTkFrame(self, fg_color="transparent")
        meta.pack(fill="x", padx=AppTheme.CARD_PAD, pady=(0, 4))

        cat_lbl = ctk.CTkLabel(
            meta,
            text=p.category,
            font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_XS),
            text_color=AppTheme.FG_MUTED,
        )
        cat_lbl.pack(side="left")

        role_badge = ctk.CTkLabel(
            meta,
            text=f" {p.role.value.upper()} ",
            font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_XS, "bold"),
            text_color=role_fg,
            fg_color=role_bg,
            corner_radius=4,
        )
        role_badge.pack(side="left", padx=(6, 0))

        # --- Content preview ---
        preview = p.content[:80].replace("\n", " ") + ("…" if len(p.content) > 80 else "")
        content_lbl = ctk.CTkLabel(
            self,
            text=preview,
            font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_SM),
            text_color=AppTheme.FG_MUTED,
            anchor="w",
            wraplength=240,
            justify="left",
        )
        content_lbl.pack(fill="x", padx=AppTheme.CARD_PAD, pady=(0, 6))

        # --- Action buttons ---
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=AppTheme.CARD_PAD, pady=(0, AppTheme.CARD_PAD))

        ctk.CTkButton(
            actions, text="📋 Copy", width=70, height=26,
            fg_color=AppTheme.BTN_COPY_BG, text_color=AppTheme.BTN_COPY_FG,
            hover_color=AppTheme.BG_HOVER,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM),
            corner_radius=AppTheme.BTN_CORNER,
            command=self._handle_copy,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            actions, text="✏ Edit", width=60, height=26,
            fg_color=AppTheme.BTN_SECONDARY_BG, text_color=AppTheme.FG_MUTED,
            hover_color=AppTheme.BG_HOVER,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM),
            corner_radius=AppTheme.BTN_CORNER,
            command=self._handle_edit,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            actions, text="🗑", width=32, height=26,
            fg_color=AppTheme.BTN_DANGER_BG, text_color=AppTheme.FG_WARN,
            hover_color="#4a1a1a",
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM),
            corner_radius=AppTheme.BTN_CORNER,
            command=self._handle_delete,
        ).pack(side="left")

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _handle_copy(self) -> None:
        self._on_copy(self._prompt)

    def _handle_delete(self) -> None:
        self._on_delete(self._prompt.id)

    def _handle_edit(self) -> None:
        self._on_edit(self._prompt)

    def _handle_favourite(self) -> None:
        self._on_favourite(self._prompt.id)

    @property
    def prompt(self) -> Prompt:
        return self._prompt
