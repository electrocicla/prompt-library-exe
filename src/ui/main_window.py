"""
MainWindow – application root window.

Responsibility: create the top-level window, wire all services together,
lay out the two panels in a drag-resizable PanedWindow, provide panel
toggle controls, and persist window geometry + sash position between
sessions. Delegates all behaviour to panels and services.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import tkinter as tk
from typing import Optional

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


def _settings_path() -> pathlib.Path:
    """Return path to the persistent UI settings JSON file."""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return pathlib.Path(base) / "NotMetaPromptLibrary" / "settings.json"


class MainWindow(ctk.CTk):
    """Root application window with resizable, toggleable library + compose panels."""

    _MIN_LIB_WIDTH: int = 260
    _MIN_COMPOSE_WIDTH: int = 340
    _DEFAULT_LIB_WIDTH: int = 420

    def __init__(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        super().__init__()

        self.title("Not-Meta Prompt Library")
        self.geometry("1200x800")
        self.minsize(480, 480)
        self.configure(fg_color=AppTheme.BG_ROOT)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._set_icon()

        # Panel visibility state
        self._lib_visible: bool = True
        self._compose_visible: bool = True

        # ── Services ──────────────────────────────────────────────────
        storage = StorageService()
        prompt_svc = PromptService(storage)
        compose_svc = ComposeService()
        clip_svc = ClipboardService(self)

        # ── Control bar (panel toggles + shortcut hints) ───────────────
        self._build_control_bar()

        # ── Resizable PanedWindow ─────────────────────────────────────
        # background= sets the sash colour; sashwidth= controls grab area.
        self._paned = tk.PanedWindow(
            self,
            orient=tk.HORIZONTAL,
            sashwidth=6,
            sashrelief=tk.FLAT,
            sashcursor="sb_h_double_arrow",
            background=AppTheme.BORDER,
            bd=0,
            relief=tk.FLAT,
        )
        self._paned.pack(fill="both", expand=True)

        # ── Panels ────────────────────────────────────────────────────
        self._library_panel = LibraryPanel(
            self._paned,
            prompt_service=prompt_svc,
            clipboard=clip_svc,
            storage=storage,
        )
        self._paned.add(
            self._library_panel,
            minsize=self._MIN_LIB_WIDTH,
            width=self._DEFAULT_LIB_WIDTH,
            stretch="always",
            sticky="nsew",
        )

        self._compose_panel = ComposePanel(
            self._paned,
            prompt_service=prompt_svc,
            compose_service=compose_svc,
            clipboard=clip_svc,
        )
        self._paned.add(
            self._compose_panel,
            minsize=self._MIN_COMPOSE_WIDTH,
            stretch="always",
            sticky="nsew",
        )

        # Save sash position whenever the user releases a drag
        self._paned.bind("<ButtonRelease-1>", lambda _e: self._save_settings())

        # Load persisted geometry + sash after the window is drawn
        self.after(60, self._load_settings)

        self._setup_shortcuts()

    # ------------------------------------------------------------------
    # Control bar
    # ------------------------------------------------------------------

    def _build_control_bar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color=AppTheme.BG_ROOT, corner_radius=0, height=40)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        self._lib_toggle_btn = ctk.CTkButton(
            bar,
            text="◀ Library",
            width=110,
            height=28,
            fg_color=AppTheme.BTN_PRIMARY_BG,
            text_color=AppTheme.BTN_PRIMARY_FG,
            hover_color=AppTheme.BTN_PRIMARY_HOVER,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_XS, "bold"),
            corner_radius=AppTheme.BTN_CORNER,
            command=self._toggle_library,
        )
        self._lib_toggle_btn.pack(side="left", padx=(10, 4), pady=6)

        self._compose_toggle_btn = ctk.CTkButton(
            bar,
            text="Compose ▶",
            width=110,
            height=28,
            fg_color=AppTheme.BTN_PRIMARY_BG,
            text_color=AppTheme.BTN_PRIMARY_FG,
            hover_color=AppTheme.BTN_PRIMARY_HOVER,
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_XS, "bold"),
            corner_radius=AppTheme.BTN_CORNER,
            command=self._toggle_compose,
        )
        self._compose_toggle_btn.pack(side="right", padx=(4, 10), pady=6)

        ctk.CTkLabel(
            bar,
            text="Ctrl+[ / Ctrl+]  toggle panels  •  Ctrl+N  new  •  Ctrl+F  search  •  Ctrl+E  compose & copy",
            font=(AppTheme.FONT_FAMILY_UI, AppTheme.FONT_SIZE_XS),
            text_color=AppTheme.FG_MUTED,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkFrame(self, fg_color=AppTheme.DIVIDER_COLOR, height=1, corner_radius=0).pack(
            fill="x", side="top"
        )

    # ------------------------------------------------------------------
    # Panel toggles
    # ------------------------------------------------------------------

    def _toggle_library(self) -> None:
        """Show or hide the library panel (Ctrl+[)."""
        if self._lib_visible:
            self._paned.forget(self._library_panel)
            self._lib_visible = False
            self._lib_toggle_btn.configure(
                text="▶ Library",
                fg_color=AppTheme.BTN_SECONDARY_BG,
                text_color=AppTheme.FG_MUTED,
                hover_color=AppTheme.BG_HOVER,
            )
        else:
            if self._compose_visible:
                self._paned.add(
                    self._library_panel,
                    minsize=self._MIN_LIB_WIDTH,
                    width=self._DEFAULT_LIB_WIDTH,
                    stretch="always",
                    sticky="nsew",
                    before=self._compose_panel,
                )
            else:
                self._paned.add(
                    self._library_panel,
                    minsize=self._MIN_LIB_WIDTH,
                    width=self._DEFAULT_LIB_WIDTH,
                    stretch="always",
                    sticky="nsew",
                )
            self._lib_visible = True
            self._lib_toggle_btn.configure(
                text="◀ Library",
                fg_color=AppTheme.BTN_PRIMARY_BG,
                text_color=AppTheme.BTN_PRIMARY_FG,
                hover_color=AppTheme.BTN_PRIMARY_HOVER,
            )
        self._save_settings()

    def _toggle_compose(self) -> None:
        """Show or hide the compose panel (Ctrl+])."""
        if self._compose_visible:
            self._paned.forget(self._compose_panel)
            self._compose_visible = False
            self._compose_toggle_btn.configure(
                text="Compose ◀",
                fg_color=AppTheme.BTN_SECONDARY_BG,
                text_color=AppTheme.FG_MUTED,
                hover_color=AppTheme.BG_HOVER,
            )
        else:
            self._paned.add(
                self._compose_panel,
                minsize=self._MIN_COMPOSE_WIDTH,
                stretch="always",
                sticky="nsew",
            )
            self._compose_visible = True
            self._compose_toggle_btn.configure(
                text="Compose ▶",
                fg_color=AppTheme.BTN_PRIMARY_BG,
                text_color=AppTheme.BTN_PRIMARY_FG,
                hover_color=AppTheme.BTN_PRIMARY_HOVER,
            )
        self._save_settings()

    # ------------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------------

    def _setup_shortcuts(self) -> None:
        """Bind all global keyboard shortcuts."""
        self.bind_all("<Control-n>", lambda _e: self._library_panel.open_create_dialog())
        self.bind_all("<Control-f>", lambda _e: self._library_panel.focus_search())
        self.bind_all("<Control-e>", lambda _e: self._compose_panel.compose_and_copy())
        self.bind_all("<Control-bracketleft>", lambda _e: self._toggle_library())
        self.bind_all("<Control-bracketright>", lambda _e: self._toggle_compose())
        self.bind_all("<Control-w>", lambda _e: self._on_close())

    # ------------------------------------------------------------------
    # Settings persistence
    # ------------------------------------------------------------------

    def _load_settings(self) -> None:
        """Restore geometry, sash position and panel visibility from last session."""
        try:
            path = _settings_path()
            if not path.exists():
                return
            raw: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))

            geometry = raw.get("geometry")
            if isinstance(geometry, str) and geometry:
                self.geometry(geometry)

            sash_pos = raw.get("sash_pos")
            if isinstance(sash_pos, int) and self._lib_visible and self._compose_visible:
                self.after(120, lambda: self._paned.sash_place(0, sash_pos, 0))

            if raw.get("lib_visible") is False:
                self.after(200, self._toggle_library)
            if raw.get("compose_visible") is False:
                self.after(220, self._toggle_compose)

        except Exception:  # noqa: BLE001 – intentional: never crash on bad settings
            pass

    def _save_settings(self) -> None:
        """Persist geometry, sash position and panel visibility."""
        try:
            sash_pos: Optional[int] = None
            if self._lib_visible and self._compose_visible:
                try:
                    coord: tuple[int, int] = self._paned.sash_coord(0)
                    sash_pos = coord[0]
                except tk.TclError:
                    pass

            settings: dict[str, object] = {
                "geometry": self.geometry(),
                "sash_pos": sash_pos,
                "lib_visible": self._lib_visible,
                "compose_visible": self._compose_visible,
            }
            path = _settings_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(settings, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:  # noqa: BLE001
            pass

    def _on_close(self) -> None:
        self._save_settings()
        self.destroy()

    # ------------------------------------------------------------------
    # Icon
    # ------------------------------------------------------------------

    def _set_icon(self) -> None:
        ico_path = _assets_dir() / "icon.ico"
        if ico_path.exists():
            try:
                self.iconbitmap(str(ico_path))
            except Exception:  # noqa: BLE001
                pass
