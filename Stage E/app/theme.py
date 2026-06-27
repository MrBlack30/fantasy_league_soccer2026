"""
theme.py - Central colour palette, fonts and ttk.Treeview styling so the whole
app shares one consistent, modern dark look.
"""
import tkinter.font as tkfont
from tkinter import ttk

# ---- Palette (dark, football-pitch inspired) ----
BG_DARK      = "#0e1117"   # window background
BG_PANEL     = "#161b22"   # sidebar / panels
CARD         = "#1c2433"   # cards
CARD_HOVER   = "#222c3d"
ACCENT       = "#2fa572"   # primary green
ACCENT_HOVER = "#268a5f"
ACCENT2      = "#7c5cff"   # secondary purple
ACCENT2_HOVER= "#6a49ec"
TEXT         = "#e6edf3"
SUBTEXT      = "#9aa4b2"
BORDER       = "#2a3340"
DANGER       = "#e5534b"
DANGER_HOVER = "#c93c34"
GRID_EVEN    = "#161d29"
GRID_ODD     = "#1b2330"
GRID_SEL     = "#2fa572"
HEADER_BG    = "#222c3d"

FONT_FAMILY = "Segoe UI"


def f(size, weight="normal"):
    return (FONT_FAMILY, size, weight)


def style_treeview(root):
    """Apply a dark, roomy style to ttk.Treeview (used for all data grids)."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(
        "Fantasy.Treeview",
        background=GRID_ODD,
        fieldbackground=GRID_ODD,
        foreground=TEXT,
        rowheight=30,
        borderwidth=0,
        font=f(11),
    )
    style.map(
        "Fantasy.Treeview",
        background=[("selected", GRID_SEL)],
        foreground=[("selected", "#ffffff")],
    )
    style.configure(
        "Fantasy.Treeview.Heading",
        background=HEADER_BG,
        foreground=TEXT,
        relief="flat",
        font=f(11, "bold"),
        padding=(8, 8),
    )
    style.map(
        "Fantasy.Treeview.Heading",
        background=[("active", ACCENT)],
        foreground=[("active", "#ffffff")],
    )
    # Scrollbars
    for name in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
        style.configure(name, background=BORDER, troughcolor=BG_PANEL,
                        bordercolor=BG_PANEL, arrowcolor=SUBTEXT)
    return style
