"""
CreatePromptDialog – modal for creating or editing a prompt.

Responsibility: collect prompt data from the user and return it.
Does NOT call any service directly; returns a result dict or None
so the caller (LibraryPanel) decides what to do with it.
"""

from __future__ import annotations

from typing import Optional
import customtkinter as ctk

from models.prompt import Prompt, PromptRole
from ui.app_theme import AppTheme

# Result returned to caller
PromptFormResult = dict  # {name, content, role, category}


class CreatePromptDialog(ctk.CTkToplevel):
    """Modal dialog for creating or editing a prompt entry."""

    def __init__(self, master, existing: Optional[Prompt] = None) -> None:
        super().__init__(master)
        self._result: Optional[PromptFormResult] = None
        self._is_edit = existing is not None
        self._existing = existing

        title = "Edit Prompt" if self._is_edit else "New Prompt"
        self.title(title)
        self.geometry("480x480")
        self.resizable(False, False)
        self.configure(fg_color=AppTheme.BG_PANEL)
        self.transient(master)
        self.grab_set()

        self._build(existing)
        self.after(100, self._center)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self, existing: Optional[Prompt]) -> None:
        pad = AppTheme.PANEL_PAD

        ctk.CTkLabel(
            self,
            text="Edit Prompt" if self._is_edit else "Create New Prompt",
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_LG, "bold"),
            text_color=AppTheme.FG_ACCENT,
        ).pack(pady=(pad, 4), padx=pad, anchor="w")

        # --- Name ---
        ctk.CTkLabel(self, text="Name", text_color=AppTheme.FG_MUTED,
                     font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM)).pack(anchor="w", padx=pad)
        self._name_var = ctk.StringVar(value=existing.name if existing else "")
        ctk.CTkEntry(
            self, textvariable=self._name_var, placeholder_text="Prompt name…",
            fg_color=AppTheme.BG_INPUT, border_color=AppTheme.BORDER,
            text_color=AppTheme.FG_MAIN, height=34,
        ).pack(fill="x", padx=pad, pady=(2, 8))

        # --- Content ---
        ctk.CTkLabel(self, text="Content", text_color=AppTheme.FG_MUTED,
                     font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM)).pack(anchor="w", padx=pad)
        self._content_text = ctk.CTkTextbox(
            self,
            fg_color=AppTheme.BG_INPUT, border_color=AppTheme.BORDER,
            text_color=AppTheme.FG_MAIN, height=160,
            font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_SM),
        )
        self._content_text.pack(fill="x", padx=pad, pady=(2, 8))
        if existing:
            self._content_text.insert("1.0", existing.content)

        # --- Role ---
        ctk.CTkLabel(self, text="Role", text_color=AppTheme.FG_MUTED,
                     font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM)).pack(anchor="w", padx=pad)
        self._role_var = ctk.StringVar(value=existing.role.value if existing else "body")
        role_frame = ctk.CTkFrame(self, fg_color="transparent")
        role_frame.pack(fill="x", padx=pad, pady=(2, 8))
        for role in PromptRole:
            role_bg, role_fg = AppTheme.role_badge(role.value)
            ctk.CTkRadioButton(
                role_frame, text=role.value.capitalize(),
                variable=self._role_var, value=role.value,
                text_color=AppTheme.FG_MAIN,
                fg_color=AppTheme.FG_ACCENT, border_color=AppTheme.BORDER,
            ).pack(side="left", padx=(0, 16))

        # --- Category ---
        ctk.CTkLabel(self, text="Category", text_color=AppTheme.FG_MUTED,
                     font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM)).pack(anchor="w", padx=pad)
        self._category_var = ctk.StringVar(value=existing.category if existing else "general")
        ctk.CTkEntry(
            self, textvariable=self._category_var, placeholder_text="general",
            fg_color=AppTheme.BG_INPUT, border_color=AppTheme.BORDER,
            text_color=AppTheme.FG_MAIN, height=34,
        ).pack(fill="x", padx=pad, pady=(2, pad))

        # --- Buttons ---
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=pad, pady=(0, pad))

        ctk.CTkButton(
            btn_row,
            text="Save" if self._is_edit else "Create",
            fg_color=AppTheme.BTN_PRIMARY_BG,
            text_color=AppTheme.BTN_PRIMARY_FG,
            hover_color=AppTheme.BTN_PRIMARY_HOVER,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_MD, "bold"),
            corner_radius=AppTheme.BTN_CORNER,
            command=self._handle_save,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            btn_row, text="Cancel",
            fg_color=AppTheme.BTN_SECONDARY_BG, text_color=AppTheme.FG_MUTED,
            hover_color=AppTheme.BG_HOVER,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_MD),
            corner_radius=AppTheme.BTN_CORNER,
            command=self.destroy,
        ).pack(side="left")

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _handle_save(self) -> None:
        name = self._name_var.get().strip()
        content = self._content_text.get("1.0", "end-1c").strip()
        if not name or not content:
            return  # Simple guard – could show validation label instead

        role_str = self._role_var.get()
        try:
            role = PromptRole(role_str)
        except ValueError:
            role = PromptRole.BODY

        self._result = {
            "name": name,
            "content": content,
            "role": role,
            "category": self._category_var.get().strip() or "general",
        }
        self.destroy()

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------

    @property
    def result(self) -> Optional[PromptFormResult]:
        """None if the dialog was cancelled."""
        return self._result

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _center(self) -> None:
        self.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() - self.winfo_width()) // 2
        y = self.master.winfo_y() + (self.master.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
