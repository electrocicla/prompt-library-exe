"""
DragSortableList – drag-to-reorder checkbox list.

Responsibility: render an ordered list of prompt entries, each with a
drag handle, checkbox, name label, and a quick-copy button. Supports
mouse drag-to-reorder within the list. Fires callbacks on reorder or
check-state change. Does NOT know about persistence.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple
import customtkinter as ctk

from models.prompt import Prompt
from ui.app_theme import AppTheme

OnCheckChange = Callable[[], None]
OnReorder = Callable[[List[str]], None]      # ordered list of prompt ids
OnCopySingle = Callable[[Prompt], None]


class _ItemRow(ctk.CTkFrame):
    """One draggable row: handle + checkbox + name + copy."""

    HANDLE_TEXT = "⠿"   # braille six-dots → universal drag icon

    def __init__(
        self,
        master,
        prompt: Prompt,
        var: ctk.BooleanVar,
        on_check_change: OnCheckChange,
        on_copy: OnCopySingle,
        on_drag_start: Callable[["_ItemRow", int], None],
        on_drag_motion: Callable[[int], None],
        on_drag_release: Callable[[], None],
        role_color: str,
    ) -> None:
        super().__init__(
            master,
            fg_color=AppTheme.BG_CARD,
            corner_radius=6,
            border_width=1,
            border_color=AppTheme.BORDER,
        )
        self.prompt = prompt
        self.var = var
        self._on_check_change = on_check_change
        self._on_copy = on_copy
        self._on_drag_start = on_drag_start
        self._on_drag_motion = on_drag_motion
        self._on_drag_release = on_drag_release
        self._is_dragging = False
        self._drag_start_y = 0

        self._build(role_color)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self, role_color: str) -> None:
        # Drag handle
        handle = ctk.CTkLabel(
            self,
            text=self.HANDLE_TEXT,
            width=24,
            font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_LG),
            text_color=AppTheme.FG_MUTED,
            cursor="fleur",
        )
        handle.pack(side="left", padx=(6, 2), pady=6)

        # Bind drag events to the handle
        handle.bind("<ButtonPress-1>", self._on_press)
        handle.bind("<B1-Motion>", self._on_motion)
        handle.bind("<ButtonRelease-1>", self._on_release)

        # Checkbox
        ctk.CTkCheckBox(
            self,
            text="",
            variable=self.var,
            width=24,
            height=24,
            fg_color=AppTheme.FG_ACCENT,
            border_color=AppTheme.BORDER,
            hover_color=AppTheme.BTN_PRIMARY_HOVER,
            command=self._on_check_change,
        ).pack(side="left", padx=(0, 4))

        # Name label (full width)
        name_lbl = ctk.CTkLabel(
            self,
            text=self.prompt.name,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_MD),
            text_color=role_color,
            anchor="w",
        )
        name_lbl.pack(side="left", fill="x", expand=True, padx=(0, 4))

        # Quick-copy button
        ctk.CTkButton(
            self,
            text="📋",
            width=32, height=28,
            fg_color=AppTheme.BTN_COPY_BG,
            text_color=AppTheme.BTN_COPY_FG,
            hover_color=AppTheme.BG_HOVER,
            font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_SM),
            corner_radius=4,
            command=lambda: self._on_copy(self.prompt),
        ).pack(side="right", padx=4, pady=4)

    # ------------------------------------------------------------------
    # Drag events – delegate to parent
    # ------------------------------------------------------------------

    def _on_press(self, event) -> None:
        self._drag_start_y = event.y_root
        self._on_drag_start(self, event.y_root)

    def _on_motion(self, event) -> None:
        self._on_drag_motion(event.y_root)

    def _on_release(self, event) -> None:
        self._on_drag_release()

    # ------------------------------------------------------------------
    # Visual highlight during drag
    # ------------------------------------------------------------------

    def set_drag_highlight(self, active: bool) -> None:
        color = AppTheme.BG_SELECTED if active else AppTheme.BG_CARD
        border = AppTheme.FG_ACCENT if active else AppTheme.BORDER
        self.configure(fg_color=color, border_color=border)

    def set_drop_target_highlight(self, active: bool) -> None:
        color = "#1a2a3a" if active else AppTheme.BG_CARD
        self.configure(fg_color=color)


class DragSortableList(ctk.CTkFrame):
    """
    Ordered list of prompt items with drag-to-reorder support.

    Maintains: ordered items list, checkbox state dict, drag state.
    Responsibilities:
      - Render rows in their current order
      - Handle drag-to-reorder via mouse events on handles
      - Expose helpers: get_checked_in_order(), set_items(), clear_all()
    """

    def __init__(
        self,
        master,
        role: str,
        on_change: OnCheckChange,
        on_copy: OnCopySingle,
        on_reorder: Optional[OnReorder] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._role = role
        self._on_change = on_change
        self._on_copy = on_copy
        self._on_reorder = on_reorder

        # State
        self._items: List[Prompt] = []               # ordered
        self._vars: Dict[str, ctk.BooleanVar] = {}   # keyed by prompt.id
        self._rows: List[_ItemRow] = []              # ordered, matching _items

        # Drag state
        self._drag_row: Optional[_ItemRow] = None
        self._drag_start_y: int = 0
        self._drag_source_index: int = -1

        _, self._role_color = AppTheme.role_badge(role)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_items(self, prompts: List[Prompt]) -> None:
        """Replace displayed items, preserving check state for existing ids."""
        new_ids = {p.id for p in prompts}
        # Remove vars for deleted items
        stale = [pid for pid in self._vars if pid not in new_ids]
        for pid in stale:
            del self._vars[pid]
        # Add vars for new items
        for p in prompts:
            if p.id not in self._vars:
                self._vars[p.id] = ctk.BooleanVar(value=False)
        self._items = list(prompts)
        self._render()

    def clear_all(self) -> None:
        """Uncheck all items."""
        for var in self._vars.values():
            var.set(False)
        self._on_change()

    def get_checked_in_order(self) -> List[Prompt]:
        """Return checked prompts in their current display order."""
        return [p for p in self._items if self._vars.get(p.id, ctk.BooleanVar()).get()]

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def _render(self) -> None:
        for row in self._rows:
            row.destroy()
        self._rows.clear()

        if not self._items:
            role_cap = self._role.capitalize()
            ctk.CTkLabel(
                self,
                text=f"No {self._role} prompts yet.\n"
                     f"Create one with role = {role_cap}.",
                text_color=AppTheme.FG_MUTED,
                font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM),
                justify="left",
            ).pack(anchor="w", padx=4, pady=4)
            return

        # Remove placeholder label if present
        for w in self.winfo_children():
            if isinstance(w, ctk.CTkLabel):
                w.destroy()

        for prompt in self._items:
            row = _ItemRow(
                self,
                prompt=prompt,
                var=self._vars[prompt.id],
                on_check_change=self._on_change,
                on_copy=self._on_copy,
                on_drag_start=self._on_drag_start,
                on_drag_motion=self._on_drag_motion,
                on_drag_release=self._on_drag_release,
                role_color=self._role_color,
            )
            row.pack(fill="x", pady=2)
            self._rows.append(row)

    # ------------------------------------------------------------------
    # Drag & Drop
    # ------------------------------------------------------------------

    def _on_drag_start(self, row: _ItemRow, y_root: int) -> None:
        self._drag_row = row
        self._drag_start_y = y_root
        try:
            self._drag_source_index = self._rows.index(row)
        except ValueError:
            self._drag_row = None
            return
        row.set_drag_highlight(True)

    def _on_drag_motion(self, y_root: int) -> None:
        if self._drag_row is None:
            return

        target_index = self._find_drop_target(y_root)
        if target_index is None or target_index == self._drag_source_index:
            self._clear_drop_highlights()
            return

        self._clear_drop_highlights()
        if 0 <= target_index < len(self._rows):
            self._rows[target_index].set_drop_target_highlight(True)

    def _on_drag_release(self) -> None:
        if self._drag_row is None:
            return

        # Find where the mouse was released
        try:
            y_root = self._drag_row.winfo_pointery()
        except Exception:
            y_root = self._drag_start_y

        target_index = self._find_drop_target(y_root)
        source_index = self._drag_source_index

        self._clear_drop_highlights()
        self._drag_row.set_drag_highlight(False)
        self._drag_row = None
        self._drag_source_index = -1

        if target_index is not None and target_index != source_index:
            self._swap_items(source_index, target_index)

    def _find_drop_target(self, y_root: int) -> Optional[int]:
        """Return which row index is closest to y_root."""
        if not self._rows:
            return None
        best_index = 0
        best_dist = float("inf")
        for i, row in enumerate(self._rows):
            try:
                row_y = row.winfo_rooty() + row.winfo_height() // 2
                dist = abs(y_root - row_y)
                if dist < best_dist:
                    best_dist = dist
                    best_index = i
            except Exception:
                continue
        return best_index

    def _swap_items(self, from_idx: int, to_idx: int) -> None:
        """Reorder items list and re-render."""
        if not (0 <= from_idx < len(self._items)) or not (0 <= to_idx < len(self._items)):
            return
        # Move item from_idx to position to_idx
        item = self._items.pop(from_idx)
        self._items.insert(to_idx, item)
        self._render()
        if self._on_reorder:
            self._on_reorder([p.id for p in self._items])
        self._on_change()

    def _clear_drop_highlights(self) -> None:
        for row in self._rows:
            row.set_drop_target_highlight(False)
