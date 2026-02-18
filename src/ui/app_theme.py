"""
AppTheme – centralised colour & font constants.

Responsibility: be the single place where all visual tokens live so
every widget imports from here instead of hardcoding hex values.
"""

from __future__ import annotations


class AppTheme:
    """Not-Meta cyberpunk dark palette."""

    # Backgrounds
    BG_ROOT = "#0a0a0f"
    BG_PANEL = "#111118"
    BG_CARD = "#16161e"
    BG_INPUT = "#1c1c28"
    BG_HOVER = "#20202e"
    BG_SELECTED = "#1a2a1a"

    # Borders
    BORDER = "#2a2a3a"
    BORDER_ACCENT = "#00c866"

    # Foregrounds
    FG_MAIN = "#e8e8f0"
    FG_MUTED = "#7a7a9a"
    FG_ACCENT = "#00ff88"
    FG_WARN = "#ff6b6b"
    FG_GOLD = "#ffd700"
    FG_BODY_BADGE = "#a0c0ff"
    FG_PREFIX_BADGE = "#80ffb0"
    FG_SUFFIX_BADGE = "#ff80aa"

    # Buttons
    BTN_PRIMARY_BG = "#00c866"
    BTN_PRIMARY_FG = "#000000"
    BTN_PRIMARY_HOVER = "#00ff88"
    BTN_SECONDARY_BG = "#1e1e2e"
    BTN_SECONDARY_FG = "#e8e8f0"
    BTN_SECONDARY_HOVER = "#2a2a3a"
    BTN_DANGER_BG = "#3a1a1a"
    BTN_DANGER_FG = "#ff6b6b"
    BTN_COPY_BG = "#1a2a3a"
    BTN_COPY_FG = "#80c8ff"

    # Scrollbar
    SCROLLBAR_BG = "#1a1a2a"
    SCROLLBAR_FG = "#3a3a5a"

    # Fonts
    FONT_FAMILY = "Consolas"
    FONT_FAMILY_UI = "Segoe UI"
    FONT_SIZE_XS = 9
    FONT_SIZE_SM = 10
    FONT_SIZE_MD = 12
    FONT_SIZE_LG = 14
    FONT_SIZE_XL = 16
    FONT_SIZE_TITLE = 18

    # Geometry
    CARD_CORNER = 8
    BTN_CORNER = 6
    PANEL_PAD = 12
    CARD_PAD = 10
    DIVIDER_COLOR = "#222230"

    # Role badge colours
    ROLE_COLORS: dict = {
        "body": ("#1a2a4a", "#80b0ff"),
        "prefix": ("#0a2a0a", "#60dd80"),
        "suffix": ("#2a0a1a", "#dd6090"),
    }

    @staticmethod
    def role_badge(role: str) -> tuple:
        """Return (bg, fg) for a role badge."""
        return AppTheme.ROLE_COLORS.get(role, ("#1a1a1a", "#aaaaaa"))
