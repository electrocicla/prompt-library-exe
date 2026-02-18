"""
MainWindow – application root window.

Responsibility: create the top-level window, wire all services
together, lay out the two panels side-by-side, and set the window
icon. Delegates all behaviour to panels and services.
"""

from __future__ import annotations

import pathlib
import sys
import customtkinter as ctk

from services.storage_service import StorageService
from services.prompt_service import PromptService
from services.compose_service import ComposeService
from services.clipboard_service import ClipboardService
from ui.app_theme import AppTheme
from ui.panels.library_panel import LibraryPanel
from ui.panels.compose_panel import ComposePanel


def _assets_dir() -> pathlib.Path:
    """Return the assets directory regardless of frozen/dev mode."""
    if getattr(sys, "frozen", False):
        base = pathlib.Path(sys.executable).parent
    else:
        base = pathlib.Path(__file__).parent.parent.parent
    return base / "assets"


class MainWindow(ctk.CTk):
    """Root application window with library + compose panels."""

    def __init__(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        super().__init__()

        self.title("Not-Meta Prompt Library")
        self.geometry("1100x720")
        self.minsize(860, 560)
        self.configure(fg_color=AppTheme.BG_ROOT)

        self._set_icon()

        # ── Services ──────────────────────────────────────────────────
        storage = StorageService()
        prompt_svc = PromptService(storage)
        compose_svc = ComposeService()
        clip_svc = ClipboardService(self)

        # ── Layout ────────────────────────────────────────────────────
        self.columnconfigure(0, weight=3, minsize=360)  # library
        self.columnconfigure(1, weight=0)               # divider
        self.columnconfigure(2, weight=4, minsize=400)  # compose
        self.rowconfigure(0, weight=1)

        library_panel = LibraryPanel(
            self,
            prompt_service=prompt_svc,
            clipboard=clip_svc,
            storage=storage,
        )
        library_panel.grid(row=0, column=0, sticky="nsew")

        # Vertical divider
        ctk.CTkFrame(self, fg_color=AppTheme.DIVIDER_COLOR, width=1, corner_radius=0).grid(
            row=0, column=1, sticky="ns"
        )

        compose_panel = ComposePanel(
            self,
            prompt_service=prompt_svc,
            compose_service=compose_svc,
            clipboard=clip_svc,
        )
        compose_panel.grid(row=0, column=2, sticky="nsew")

    # ------------------------------------------------------------------
    # Icon
    # ------------------------------------------------------------------

    def _set_icon(self) -> None:
        ico_path = _assets_dir() / "icon.ico"
        if ico_path.exists():
            try:
                self.iconbitmap(str(ico_path))
            except Exception:
                pass
