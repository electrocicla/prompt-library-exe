"""
ComposePanel – right-side prompt composition area.

Responsibility: let users select any number of prefix prompts, write
a body, select any number of suffix prompts, pick a separator, then
compose everything into a final string and copy it to clipboard.
No persistence, no terminal injection.
"""

from __future__ import annotations

from typing import Dict, List, Optional
import customtkinter as ctk

from models.prompt import Prompt, PromptRole
from models.library_state import LibraryState
from services.compose_service import ComposeService, ComposeSeparator
from services.clipboard_service import ClipboardService
from services.prompt_service import PromptService
from ui.app_theme import AppTheme

_TOAST_MS = 1800


class ComposePanel(ctk.CTkFrame):
    """Compose panel: prefix checks + body + suffix checks + copy."""

    def __init__(
        self,
        master,
        prompt_service: PromptService,
        compose_service: ComposeService,
        clipboard: ClipboardService,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color=AppTheme.BG_PANEL, corner_radius=0, **kwargs)
        self._svc = prompt_service
        self._compose = compose_service
        self._clip = clipboard
        self._toast_job: Optional[str] = None

        # Checkbox vars keyed by prompt id
        self._prefix_vars: Dict[str, ctk.BooleanVar] = {}
        self._suffix_vars: Dict[str, ctk.BooleanVar] = {}

        self._sep_var = ctk.StringVar(value=ComposeSeparator.NEWLINE.value)
        self._custom_sep_var = ctk.StringVar(value=" | ")

        self._build()
        self._svc.subscribe(self._on_state_changed)
        self._refresh_selectors()

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
            text="⚡ COMPOSE & COPY",
            font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_SM, "bold"),
            text_color=AppTheme.FG_ACCENT,
        ).pack(side="left", padx=pad, pady=8)

        # Divider
        ctk.CTkFrame(self, fg_color=AppTheme.DIVIDER_COLOR, height=1, corner_radius=0).pack(fill="x")

        # ── Scrollable content ────────────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color=AppTheme.BG_PANEL,
            scrollbar_button_color=AppTheme.SCROLLBAR_FG,
            scrollbar_button_hover_color=AppTheme.FG_ACCENT,
        )
        self._scroll.pack(fill="both", expand=True)

        # ── Prefix selectors ──────────────────────────────────────────
        self._section_header(self._scroll, "PREFIX PROMPTS", AppTheme.FG_PREFIX_BADGE,
                             "Applied before the body, in order")

        self._prefix_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._prefix_frame.pack(fill="x", padx=pad, pady=(0, 8))

        # ── Body ──────────────────────────────────────────────────────
        self._section_header(self._scroll, "BODY", AppTheme.FG_BODY_BADGE,
                             "Your custom prompt text")

        self._body_text = ctk.CTkTextbox(
            self._scroll,
            fg_color=AppTheme.BG_INPUT,
            border_color=AppTheme.BORDER_ACCENT,
            border_width=1,
            text_color=AppTheme.FG_MAIN,
            font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_SM),
            height=140,
            wrap="word",
        )
        self._body_text.pack(fill="x", padx=pad, pady=(0, 8))

        ctk.CTkButton(
            self._scroll,
            text="📋 Copy Body Only",
            height=28,
            fg_color=AppTheme.BTN_COPY_BG,
            text_color=AppTheme.BTN_COPY_FG,
            hover_color=AppTheme.BG_HOVER,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM),
            corner_radius=AppTheme.BTN_CORNER,
            command=self._copy_body_only,
        ).pack(fill="x", padx=pad, pady=(0, 8))

        # ── Suffix selectors ──────────────────────────────────────────
        self._section_header(self._scroll, "SUFFIX PROMPTS", AppTheme.FG_SUFFIX_BADGE,
                             "Appended after the body, in order")

        self._suffix_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._suffix_frame.pack(fill="x", padx=pad, pady=(0, 8))

        # ── Separator ────────────────────────────────────────────────
        self._section_header(self._scroll, "SEPARATOR", AppTheme.FG_MUTED,
                             "How parts are joined together")

        sep_frame = ctk.CTkFrame(self._scroll, fg_color=AppTheme.BG_CARD,
                                  corner_radius=AppTheme.CARD_CORNER, border_width=1,
                                  border_color=AppTheme.BORDER)
        sep_frame.pack(fill="x", padx=pad, pady=(0, 8))

        for sep in ComposeSeparator:
            ctk.CTkRadioButton(
                sep_frame,
                text=sep.label(),
                variable=self._sep_var,
                value=sep.value,
                text_color=AppTheme.FG_MAIN,
                fg_color=AppTheme.FG_ACCENT,
                border_color=AppTheme.BORDER,
                command=self._on_sep_changed,
            ).pack(anchor="w", padx=pad, pady=3)

        self._custom_sep_entry = ctk.CTkEntry(
            sep_frame,
            textvariable=self._custom_sep_var,
            placeholder_text="Custom separator…",
            fg_color=AppTheme.BG_INPUT,
            border_color=AppTheme.BORDER,
            text_color=AppTheme.FG_MAIN,
            height=30,
            state="disabled",
        )
        self._custom_sep_entry.pack(fill="x", padx=pad, pady=(0, pad))

        # ── Preview ──────────────────────────────────────────────────
        self._section_header(self._scroll, "PREVIEW", AppTheme.FG_MUTED, "")

        self._preview_lbl = ctk.CTkLabel(
            self._scroll,
            text="Select prefixes/suffixes or type a body to see preview…",
            fg_color=AppTheme.BG_CARD,
            corner_radius=AppTheme.CARD_CORNER,
            text_color=AppTheme.FG_MUTED,
            font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_SM),
            anchor="nw",
            justify="left",
            wraplength=340,
        )
        self._preview_lbl.pack(fill="x", padx=pad, pady=(0, 8))

        # ── Toast ─────────────────────────────────────────────────────
        self._toast_lbl = ctk.CTkLabel(
            self._scroll,
            text="", height=0,
            fg_color=AppTheme.BG_SELECTED,
            corner_radius=4,
            text_color=AppTheme.FG_ACCENT,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM),
        )

        # ── Compose & Copy button ─────────────────────────────────────
        ctk.CTkButton(
            self._scroll,
            text="⚡ COMPOSE & COPY",
            height=44,
            fg_color=AppTheme.BTN_PRIMARY_BG,
            text_color=AppTheme.BTN_PRIMARY_FG,
            hover_color=AppTheme.BTN_PRIMARY_HOVER,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_LG, "bold"),
            corner_radius=AppTheme.BTN_CORNER,
            command=self._handle_compose_and_copy,
        ).pack(fill="x", padx=pad, pady=(0, pad))

        # Bind body changes to preview
        self._body_text.bind("<KeyRelease>", lambda _: self._update_preview())

    # ------------------------------------------------------------------
    # Section header helper
    # ------------------------------------------------------------------

    @staticmethod
    def _section_header(parent, title: str, color: str, subtitle: str) -> None:
        pad = AppTheme.PANEL_PAD
        lbl_frame = ctk.CTkFrame(parent, fg_color="transparent")
        lbl_frame.pack(fill="x", padx=pad, pady=(8, 2))
        ctk.CTkLabel(
            lbl_frame,
            text=title,
            font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_XS, "bold"),
            text_color=color,
        ).pack(side="left")
        if subtitle:
            ctk.CTkLabel(
                lbl_frame,
                text=f"  {subtitle}",
                font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_XS),
                text_color=AppTheme.FG_MUTED,
            ).pack(side="left")

    # ------------------------------------------------------------------
    # Refresh selectors when library changes
    # ------------------------------------------------------------------

    def _refresh_selectors(self, _state: Optional[LibraryState] = None) -> None:
        self._rebuild_selector(
            self._prefix_frame,
            self._svc.get_by_role(PromptRole.PREFIX),
            self._prefix_vars,
            role="prefix",
        )
        self._rebuild_selector(
            self._suffix_frame,
            self._svc.get_by_role(PromptRole.SUFFIX),
            self._suffix_vars,
            role="suffix",
        )
        self._update_preview()

    def _rebuild_selector(
        self,
        frame: ctk.CTkFrame,
        prompts: List[Prompt],
        var_map: Dict[str, ctk.BooleanVar],
        role: str,
    ) -> None:
        # Remove old widgets
        for w in frame.winfo_children():
            w.destroy()

        if not prompts:
            _, badge_fg = AppTheme.role_badge(role)
            ctk.CTkLabel(
                frame,
                text=f"No {role} prompts yet.\nCreate one in the library with role = {role.capitalize()}.",
                text_color=AppTheme.FG_MUTED,
                font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM),
                justify="left",
            ).pack(anchor="w")
            return

        # Keep existing BooleanVars where possible
        current_ids = {p.id for p in prompts}
        stale = [pid for pid in var_map if pid not in current_ids]
        for pid in stale:
            del var_map[pid]

        _, badge_fg = AppTheme.role_badge(role)
        for prompt in prompts:
            if prompt.id not in var_map:
                var_map[prompt.id] = ctk.BooleanVar(value=False)

            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", pady=1)

            ctk.CTkCheckBox(
                row,
                text=prompt.name,
                variable=var_map[prompt.id],
                font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_SM),
                text_color=AppTheme.FG_MAIN,
                fg_color=AppTheme.FG_ACCENT,
                border_color=AppTheme.BORDER,
                hover_color=AppTheme.BTN_PRIMARY_HOVER,
                command=self._update_preview,
            ).pack(side="left")

            # Small copy button next to each checkbox
            ctk.CTkButton(
                row,
                text="📋",
                width=28, height=22,
                fg_color=AppTheme.BTN_COPY_BG,
                text_color=AppTheme.BTN_COPY_FG,
                hover_color=AppTheme.BG_HOVER,
                font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_XS),
                corner_radius=4,
                command=lambda p=prompt: self._copy_single(p),
            ).pack(side="left", padx=(6, 0))

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def _update_preview(self) -> None:
        prefixes = self._selected_prompts(PromptRole.PREFIX, self._prefix_vars)
        suffixes = self._selected_prompts(PromptRole.SUFFIX, self._suffix_vars)
        body = self._body_text.get("1.0", "end-1c")
        sep, custom = self._current_separator()

        preview = self._compose.preview(prefixes, body, suffixes, sep, custom)
        display = preview if preview.strip() else "Select prefixes/suffixes or type a body…"
        self._preview_lbl.configure(text=display, text_color=AppTheme.FG_MAIN if preview.strip() else AppTheme.FG_MUTED)

    # ------------------------------------------------------------------
    # Compose & Copy
    # ------------------------------------------------------------------

    def _handle_compose_and_copy(self) -> None:
        prefixes = self._selected_prompts(PromptRole.PREFIX, self._prefix_vars)
        suffixes = self._selected_prompts(PromptRole.SUFFIX, self._suffix_vars)
        body = self._body_text.get("1.0", "end-1c")
        sep, custom = self._current_separator()

        composed = self._compose.compose(prefixes, body, suffixes, sep, custom)
        if not composed.strip():
            self._toast("Nothing to copy — add prefixes, body, or suffixes first.")
            return

        # Increment usage for all selected
        for prompt in prefixes + suffixes:
            self._svc.increment_usage(prompt.id)

        if self._clip.copy(composed):
            parts = []
            if prefixes:
                parts.append(f"{len(prefixes)} prefix{'es' if len(prefixes) > 1 else ''}")
            if body.strip():
                parts.append("body")
            if suffixes:
                parts.append(f"{len(suffixes)} suffix{'es' if len(suffixes) > 1 else ''}")
            self._toast("Composed & copied: " + " + ".join(parts))
        else:
            self._toast("Clipboard write failed.")

    def _copy_body_only(self) -> None:
        body = self._body_text.get("1.0", "end-1c")
        if body.strip() and self._clip.copy(body):
            self._toast("Body copied.")

    def _copy_single(self, prompt: Prompt) -> None:
        if self._clip.copy(prompt.content):
            self._svc.increment_usage(prompt.id)
            self._toast(f"Copied: {prompt.name}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _selected_prompts(
        self, role: PromptRole, var_map: Dict[str, ctk.BooleanVar]
    ) -> List[Prompt]:
        all_by_role = {p.id: p for p in self._svc.get_by_role(role)}
        return [all_by_role[pid] for pid, var in var_map.items() if var.get() and pid in all_by_role]

    def _current_separator(self):
        sep_val = self._sep_var.get()
        try:
            sep = ComposeSeparator(sep_val)
        except ValueError:
            sep = ComposeSeparator.NEWLINE
        custom = self._custom_sep_var.get()
        return sep, custom

    def _on_sep_changed(self) -> None:
        is_custom = self._sep_var.get() == ComposeSeparator.CUSTOM.value
        state = "normal" if is_custom else "disabled"
        self._custom_sep_entry.configure(state=state)
        self._update_preview()

    # ------------------------------------------------------------------
    # Observer
    # ------------------------------------------------------------------

    def _on_state_changed(self, state: LibraryState) -> None:
        self._refresh_selectors(state)

    # ------------------------------------------------------------------
    # Toast
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
