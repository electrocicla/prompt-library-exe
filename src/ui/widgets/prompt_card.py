"""
PromptCard – single prompt entry widget.

Responsibility: render one prompt with its metadata and action buttons.
v1.1: Supports inline editing of name and content (double-click to edit,
      Enter / Ctrl+Enter / focus-out to commit). Fires callbacks for all
      mutations; does NOT persist directly.
"""

from __future__ import annotations

from typing import Callable, Optional
import customtkinter as ctk

from models.prompt import Prompt, PromptRole
from ui.app_theme import AppTheme

# Callback type aliases for clarity
OnCopy        = Callable[[Prompt], None]
OnDelete      = Callable[[str], None]
OnEdit        = Callable[[Prompt], None]
OnFavourite   = Callable[[str], None]
OnRoleChange  = Callable[[str, PromptRole], None]
OnInlineEdit  = Callable[[str, str, str], None]   # (prompt_id, field, new_value)


class PromptCard(ctk.CTkFrame):
    """One prompt card shown in the library list. v1.1 supports inline editing."""

    def __init__(
        self,
        master,
        prompt: Prompt,
        on_copy: OnCopy,
        on_delete: OnDelete,
        on_edit: OnEdit,
        on_favourite: OnFavourite,
        on_role_change: OnRoleChange,
        on_inline_edit: Optional[OnInlineEdit] = None,
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
        self._on_inline_edit = on_inline_edit

        # Inline-edit state
        self._name_editing = False
        self._content_editing = False
        self._name_lbl: Optional[ctk.CTkLabel] = None
        self._name_entry: Optional[ctk.CTkEntry] = None
        self._content_lbl: Optional[ctk.CTkLabel] = None
        self._content_entry: Optional[ctk.CTkTextbox] = None
        self._content_hint: Optional[ctk.CTkLabel] = None

        self._build()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        p = self._prompt
        role_bg, role_fg = AppTheme.role_badge(p.role.value)
        pad = AppTheme.CARD_PAD

        # --- Header row ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=pad, pady=(pad, 4))
        header.columnconfigure(1, weight=1)

        # Favourite star
        star_text = "★" if p.is_favorite else "☆"
        star_color = AppTheme.FG_GOLD if p.is_favorite else AppTheme.FG_MUTED
        self._star_btn = ctk.CTkButton(
            header, text=star_text, width=24, height=24,
            fg_color="transparent", text_color=star_color,
            hover_color=AppTheme.BG_HOVER,
            font=(AppTheme.FONT_FAMILY, 14),
            command=self._handle_favourite,
        )
        self._star_btn.grid(row=0, column=0, padx=(0, 6))

        # Name label (double-click → inline edit)
        self._name_lbl = ctk.CTkLabel(
            header,
            text=p.name,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_MD, "bold"),
            text_color=AppTheme.FG_MAIN,
            anchor="w",
            cursor="xterm",
        )
        self._name_lbl.grid(row=0, column=1, sticky="ew")
        self._name_lbl.bind("<Double-Button-1>", lambda _: self._start_name_edit())
        self._name_lbl.bind("<Enter>", lambda _: self._name_lbl.configure(text_color=AppTheme.FG_ACCENT) if not self._name_editing else None)
        self._name_lbl.bind("<Leave>", lambda _: self._name_lbl.configure(text_color=AppTheme.FG_MAIN) if not self._name_editing else None)

        # Usage count badge
        ctk.CTkLabel(
            header,
            text=f"×{p.usage_count}",
            font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_XS),
            text_color=AppTheme.FG_MUTED,
        ).grid(row=0, column=2, padx=(6, 0))

        # --- Category + role row ---
        meta = ctk.CTkFrame(self, fg_color="transparent")
        meta.pack(fill="x", padx=pad, pady=(0, 4))

        ctk.CTkLabel(
            meta,
            text=p.category,
            font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_XS),
            text_color=AppTheme.FG_MUTED,
        ).pack(side="left")

        ctk.CTkLabel(
            meta,
            text=f" {p.role.value.upper()} ",
            font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_XS, "bold"),
            text_color=role_fg,
            fg_color=role_bg,
            corner_radius=4,
        ).pack(side="left", padx=(6, 0))

        ctk.CTkLabel(
            meta,
            text="  ✎ dbl-click to edit",
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_XS),
            text_color="#3a3a5a",
        ).pack(side="left", padx=(8, 0))

        # --- Content preview (double-click → inline edit) ---
        self._content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._content_frame.pack(fill="x", padx=pad, pady=(0, 6))

        preview = p.content[:80].replace("\n", " ") + ("…" if len(p.content) > 80 else "")
        self._content_lbl = ctk.CTkLabel(
            self._content_frame,
            text=preview,
            font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_SM),
            text_color=AppTheme.FG_MUTED,
            anchor="w",
            wraplength=240,
            justify="left",
            cursor="xterm",
        )
        self._content_lbl.pack(fill="x")
        self._content_lbl.bind("<Double-Button-1>", lambda _: self._start_content_edit())
        self._content_lbl.bind("<Enter>", lambda _: self._content_lbl.configure(text_color=AppTheme.FG_MAIN) if not self._content_editing else None)
        self._content_lbl.bind("<Leave>", lambda _: self._content_lbl.configure(text_color=AppTheme.FG_MUTED) if not self._content_editing else None)

        # --- Action buttons ---
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=pad, pady=(0, pad))

        ctk.CTkButton(
            actions, text="📋 Copy", width=70, height=26,
            fg_color=AppTheme.BTN_COPY_BG, text_color=AppTheme.BTN_COPY_FG,
            hover_color=AppTheme.BG_HOVER,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM),
            corner_radius=AppTheme.BTN_CORNER,
            command=self._handle_copy,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            actions, text="✏ Full Edit", width=76, height=26,
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
    # Inline name editing
    # ------------------------------------------------------------------

    def _start_name_edit(self) -> None:
        if self._name_editing or self._name_lbl is None:
            return
        self._name_editing = True
        self._name_lbl.grid_remove()

        self._name_entry = ctk.CTkEntry(
            self._name_lbl.master,
            fg_color=AppTheme.BG_INPUT,
            border_color=AppTheme.BORDER_ACCENT,
            border_width=1,
            text_color=AppTheme.FG_MAIN,
            height=26,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_MD, "bold"),
        )
        self._name_entry.insert(0, self._prompt.name)
        self._name_entry.grid(row=0, column=1, sticky="ew")
        self._name_entry.focus_set()
        self._name_entry.select_range(0, "end")
        self._name_entry.bind("<Return>", lambda _: self._commit_name_edit())
        self._name_entry.bind("<Escape>", lambda _: self._cancel_name_edit())
        self._name_entry.bind("<FocusOut>", lambda _: self._commit_name_edit())

    def _commit_name_edit(self) -> None:
        if not self._name_editing or self._name_entry is None:
            return
        new_name = self._name_entry.get().strip()
        self._name_editing = False
        self._name_entry.destroy()
        self._name_entry = None
        if new_name and new_name != self._prompt.name and self._on_inline_edit:
            self._on_inline_edit(self._prompt.id, "name", new_name)
            if self._name_lbl:
                self._name_lbl.configure(text=new_name)
        if self._name_lbl:
            self._name_lbl.grid()

    def _cancel_name_edit(self) -> None:
        if not self._name_editing or self._name_entry is None:
            return
        self._name_editing = False
        self._name_entry.destroy()
        self._name_entry = None
        if self._name_lbl:
            self._name_lbl.grid()

    # ------------------------------------------------------------------
    # Inline content editing
    # ------------------------------------------------------------------

    def _start_content_edit(self) -> None:
        if self._content_editing or self._content_lbl is None:
            return
        self._content_editing = True
        self._content_lbl.pack_forget()

        self._content_entry = ctk.CTkTextbox(
            self._content_frame,
            fg_color=AppTheme.BG_INPUT,
            border_color=AppTheme.BORDER_ACCENT,
            border_width=1,
            text_color=AppTheme.FG_MAIN,
            font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_SM),
            height=100,
            wrap="word",
        )
        self._content_entry.insert("1.0", self._prompt.content)
        self._content_entry.pack(fill="x")
        self._content_entry.focus_set()

        self._content_hint = ctk.CTkLabel(
            self._content_frame,
            text="  Ctrl+Enter to save  ·  Esc to cancel",
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_XS),
            text_color=AppTheme.FG_MUTED,
        )
        self._content_hint.pack(anchor="w")

        self._content_entry.bind("<Control-Return>", lambda _: self._commit_content_edit())
        self._content_entry.bind("<Escape>", lambda _: self._cancel_content_edit())
        self._content_entry.bind("<FocusOut>", lambda _: self._commit_content_edit())

    def _commit_content_edit(self) -> None:
        if not self._content_editing or self._content_entry is None:
            return
        new_content = self._content_entry.get("1.0", "end-1c").strip()
        self._content_editing = False
        self._content_entry.destroy()
        self._content_entry = None
        if self._content_hint:
            self._content_hint.destroy()
            self._content_hint = None
        if new_content and new_content != self._prompt.content and self._on_inline_edit:
            self._on_inline_edit(self._prompt.id, "content", new_content)
            preview = new_content[:80].replace("\n", " ") + ("…" if len(new_content) > 80 else "")
            if self._content_lbl:
                self._content_lbl.configure(text=preview)
        if self._content_lbl:
            self._content_lbl.pack(fill="x")

    def _cancel_content_edit(self) -> None:
        if not self._content_editing or self._content_entry is None:
            return
        self._content_editing = False
        self._content_entry.destroy()
        self._content_entry = None
        if self._content_hint:
            self._content_hint.destroy()
            self._content_hint = None
        if self._content_lbl:
            self._content_lbl.pack(fill="x")

    # ------------------------------------------------------------------
    # Standard handlers
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
