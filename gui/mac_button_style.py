from __future__ import annotations

from tkinter import ttk


def apply_mac_button_style(style: ttk.Style | None = None) -> ttk.Style:
    """Configure ``ttk.Button`` widgets to mimic macOS capsule buttons.

    The function adjusts padding, border and relief to give buttons a rounded
    3D appearance that resembles native macOS controls.  The style changes are
    applied to the passed ``ttk.Style`` instance.  If no *style* is supplied a
    new instance is created.
    """
    style = style or ttk.Style()
    style.configure(
        "TButton",
        padding=(10, 5),
        relief="raised",
        borderwidth=1,
        foreground="black",
        background="#dbe5ff",
    )
    style.map(
        "TButton",
        background=[("active", "#87cefa"), ("pressed", "#e0ffff")],
        relief=[("pressed", "sunken"), ("!pressed", "raised")],
    )
    return style
