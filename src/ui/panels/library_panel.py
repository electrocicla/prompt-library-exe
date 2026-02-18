"""
LibraryPanel – left-side scrollable prompt library.

Responsibility: display ranked/filtered prompt cards, toolbar with
search + create + import/export. Delegates state mutations to
PromptService and clipboard to ClipboardService. Fires a callback
when selection changes so ComposePanel can refresh.
"""

from __future__ import annotations

import json
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Callable, List, Optional

import customtkinter as ctk

from models.prompt import Prompt, PromptRole
from models.library_state import LibraryState
from services.prompt_service import PromptService
from services.clipboard_service import ClipboardService
from services.storage_service import StorageService
from ui.app_theme import AppTheme
from ui.widgets.prompt_card import PromptCard
from ui.dialogs.create_prompt_dialog import CreatePromptDialog


OnSelectionChanged = Callable[[List[Prompt]], None]
_TOAST_MS = 1800
_ALL_CHIP = "All"


class LibraryPanel(ctk.CTkFrame):
    """Scrollable prompt library with toolbar."""

    def __init__(
        self,
        master,
        prompt_service: PromptService,
        clipboard: ClipboardService,
        storage: StorageService,
        on_selection_changed: Optional[OnSelectionChanged] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color=AppTheme.BG_PANEL, corner_radius=0, **kwargs)
        self._svc = prompt_service
        self._clip = clipboard
        self._storage = storage
        self._on_selection_changed = on_selection_changed
        self._toast_job: Optional[str] = None
        self._cards: List[PromptCard] = []
        self._active_category: Optional[str] = None   # None = All
        self._search_entry: Optional[ctk.CTkEntry] = None

        self._build()
        self._svc.subscribe(self._on_state_changed)
        self._refresh_list()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        pad = AppTheme.PANEL_PAD

        # ── Header ────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=AppTheme.BG_ROOT, corner_radius=0)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="📚 PROMPT LIBRARY",
            font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_XL, "bold"),
            text_color=AppTheme.FG_ACCENT,
        ).pack(side="left", padx=pad, pady=8)

        toolbar = ctk.CTkFrame(header, fg_color="transparent")
        toolbar.pack(side="right", padx=pad, pady=4)

        ctk.CTkButton(
            toolbar, text="＋ New", width=80, height=34,
            fg_color=AppTheme.BTN_PRIMARY_BG, text_color=AppTheme.BTN_PRIMARY_FG,
            hover_color=AppTheme.BTN_PRIMARY_HOVER,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM, "bold"),
            corner_radius=AppTheme.BTN_CORNER,
            command=self._open_create_dialog,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            toolbar, text="⬆ Import", width=86, height=34,
            fg_color=AppTheme.BTN_SECONDARY_BG, text_color=AppTheme.FG_MUTED,
            hover_color=AppTheme.BG_HOVER,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM),
            corner_radius=AppTheme.BTN_CORNER,
            command=self._handle_import,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            toolbar, text="⬇ Export", width=86, height=34,
            fg_color=AppTheme.BTN_SECONDARY_BG, text_color=AppTheme.FG_MUTED,
            hover_color=AppTheme.BG_HOVER,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM),
            corner_radius=AppTheme.BTN_CORNER,
            command=self._handle_export,
        ).pack(side="left")

        # ── Search ────────────────────────────────────────────────────
        search_frame = ctk.CTkFrame(self, fg_color=AppTheme.BG_ROOT, corner_radius=0)
        search_frame.pack(fill="x")

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._refresh_list())
        self._search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self._search_var,
            placeholder_text="🔍  Search prompts…  (Ctrl+F)",
            fg_color=AppTheme.BG_INPUT,
            border_color=AppTheme.BORDER,
            text_color=AppTheme.FG_MAIN,
            height=40,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM),
        )
        self._search_entry.pack(fill="x", padx=pad, pady=8)

        # ── Category chip filter ──────────────────────────────────────
        self._chips_outer = ctk.CTkFrame(self, fg_color=AppTheme.BG_ROOT, corner_radius=0)
        self._chips_outer.pack(fill="x")
        self._chips_scroll = ctk.CTkScrollableFrame(
            self._chips_outer,
            fg_color="transparent",
            orientation="horizontal",
            height=36,
            scrollbar_button_color=AppTheme.SCROLLBAR_FG,
            scrollbar_button_hover_color=AppTheme.FG_ACCENT,
        )
        self._chips_scroll.pack(fill="x", padx=pad, pady=(0, 4))

        # Divider
        ctk.CTkFrame(self, fg_color=AppTheme.DIVIDER_COLOR, height=1, corner_radius=0).pack(fill="x")

        # ── Toast ─────────────────────────────────────────────────────
        self._toast_lbl = ctk.CTkLabel(
            self, text="", height=0,
            fg_color=AppTheme.BG_SELECTED, corner_radius=4,
            text_color=AppTheme.FG_ACCENT,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM),
        )

        # ── Scrollable card list ───────────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=AppTheme.BG_PANEL,
            scrollbar_button_color=AppTheme.SCROLLBAR_FG,
            scrollbar_button_hover_color=AppTheme.FG_ACCENT,
        )
        self._scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Footer ────────────────────────────────────────────────────
        self._stats_lbl = ctk.CTkLabel(
            self, text="",
            fg_color=AppTheme.BG_ROOT,
            text_color=AppTheme.FG_MUTED,
            font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_SM),
            anchor="w",
        )
        self._stats_lbl.pack(fill="x", padx=pad, pady=6)

    # ------------------------------------------------------------------
    # Public shortcuts API
    # ------------------------------------------------------------------

    def focus_search(self) -> None:
        """Focus the search entry (Ctrl+F)."""
        if self._search_entry:
            self._search_entry.focus_set()
            self._search_entry.select_range(0, "end")

    def open_create_dialog(self) -> None:
        """Open the new prompt dialog (Ctrl+N)."""
        self._open_create_dialog()

    # ------------------------------------------------------------------
    # Category chips
    # ------------------------------------------------------------------

    def _refresh_chips(self, prompts: List[Prompt]) -> None:
        """Rebuild category chip buttons from current prompt categories."""
        for w in self._chips_scroll.winfo_children():
            w.destroy()

        categories = [_ALL_CHIP] + sorted(
            {p.category for p in self._svc.get_all() if p.category}
        )

        for cat in categories:
            is_active = (
                cat == _ALL_CHIP and self._active_category is None
            ) or cat == self._active_category

            chip = ctk.CTkButton(
                self._chips_scroll,
                text=cat,
                height=30,
                width=max(50, len(cat) * 9),
                fg_color=AppTheme.BTN_PRIMARY_BG if is_active else AppTheme.BTN_SECONDARY_BG,
                text_color=AppTheme.BTN_PRIMARY_FG if is_active else AppTheme.FG_MUTED,
                hover_color=AppTheme.BTN_PRIMARY_HOVER,
                font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM, "bold" if is_active else "normal"),
                corner_radius=12,
                command=lambda c=cat: self._select_category(c),
            )
            chip.pack(side="left", padx=(0, 4))

    def _select_category(self, cat: str) -> None:
        self._active_category = None if cat == _ALL_CHIP else cat
        self._refresh_list()

    # ------------------------------------------------------------------
    # List rendering
    # ------------------------------------------------------------------

    def _refresh_list(self, _state: Optional[LibraryState] = None) -> None:
        # Clear old cards
        for widget in self._scroll.winfo_children():
            widget.destroy()
        self._cards.clear()

        query = self._search_var.get().strip()
        filtered = self._svc.search(query)

        # Category filter
        if self._active_category:
            filtered = [p for p in filtered if p.category == self._active_category]

        ranked = self._svc.ranked(filtered)
        self._refresh_chips(ranked)

        if not ranked:
            ctk.CTkLabel(
                self._scroll,
                text="No prompts yet.\nClick ＋ New to create one.",
                text_color=AppTheme.FG_MUTED,
                font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_MD),
                justify="center",
            ).pack(pady=48)
            self._update_stats(ranked)
            return

        for prompt in ranked:
            card = PromptCard(
                self._scroll,
                prompt=prompt,
                on_copy=self._handle_copy,
                on_delete=self._handle_delete,
                on_edit=self._handle_edit,
                on_favourite=self._handle_favourite,
                on_role_change=self._handle_role_change,
                on_inline_edit=self._handle_inline_edit,
            )
            card.pack(fill="x", padx=8, pady=3)
            self._cards.append(card)

        self._update_stats(ranked)

    def _update_stats(self, prompts: List[Prompt]) -> None:
        total = len(self._svc.get_all())
        shown = len(prompts)
        total_uses = sum(p.usage_count for p in self._svc.get_all())
        self._stats_lbl.configure(
            text=f" {shown}/{total} prompts  •  {total_uses} total uses"
        )

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _handle_copy(self, prompt: Prompt) -> None:
        if self._clip.copy(prompt.content):
            self._svc.increment_usage(prompt.id)
            self._toast(f"Copied: {prompt.name}")

    def _handle_delete(self, prompt_id: str) -> None:
        if messagebox.askyesno("Delete Prompt", "Delete this prompt permanently?", parent=self):
            self._svc.delete(prompt_id)

    def _handle_edit(self, prompt: Prompt) -> None:
        dlg = CreatePromptDialog(self.winfo_toplevel(), existing=prompt)
        self.wait_window(dlg)
        result = dlg.result
        if result:
            self._svc.update(
                prompt.id,
                name=result["name"],
                content=result["content"],
                role=result["role"].value,
                category=result["category"],
            )

    def _handle_favourite(self, prompt_id: str) -> None:
        self._svc.toggle_favorite(prompt_id)

    def _handle_role_change(self, prompt_id: str, role: PromptRole) -> None:
        self._svc.update(prompt_id, role=role.value)

    def _handle_inline_edit(self, prompt_id: str, field: str, new_value: str) -> None:
        """Commit an inline edit from a PromptCard without reopening a dialog."""
        self._svc.update(prompt_id, **{field: new_value})
        self._toast(f"Updated {field}")

    def _open_create_dialog(self) -> None:
        dlg = CreatePromptDialog(self.winfo_toplevel())
        self.wait_window(dlg)
        result = dlg.result
        if result:
            self._svc.create(
                name=result["name"],
                content=result["content"],
                role=result["role"],
                category=result["category"],
            )

    def _handle_export(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Prompt Library",
        )
        if path:
            try:
                json_str = self._storage.export_json(self._svc.state)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(json_str)
                self._toast(f"Exported to {path}")
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("Export Failed", str(exc), parent=self)

    def _handle_import(self) -> None:
        path = filedialog.askopenfilename(
            parent=self,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Import Prompt Library",
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                raw = f.read()
            new_state = self._storage.import_json(raw)
            merge = messagebox.askyesno(
                "Import Mode",
                "Merge with existing prompts?\n\n"
                "Yes = merge (keep both, skip duplicate IDs)\n"
                "No  = replace all existing prompts",
                parent=self,
            )
            self._svc.import_state(new_state, merge=merge)
            self._toast("Import complete")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Import Failed", str(exc), parent=self)

    # ------------------------------------------------------------------
    # Observer
    # ------------------------------------------------------------------

    def _on_state_changed(self, state: LibraryState) -> None:
        # If active category no longer exists in prompts, reset to All
        if self._active_category:
            categories = {p.category for p in state.prompts}
            if self._active_category not in categories:
                self._active_category = None
        self._refresh_list(state)
        if self._on_selection_changed:
            self._on_selection_changed(state.prompts)

    # ------------------------------------------------------------------
    # Toast helper
    # ------------------------------------------------------------------

    def _toast(self, message: str) -> None:
        if self._toast_job:
            self.after_cancel(self._toast_job)
        self._toast_lbl.configure(text=f"  ✓ {message}  ")
        self._toast_lbl.pack(fill="x", padx=AppTheme.PANEL_PAD, pady=(0, 4))
        self._toast_job = self.after(_TOAST_MS, self._hide_toast)

    def _hide_toast(self) -> None:
        self._toast_lbl.pack_forget()
        self._toast_job = None
