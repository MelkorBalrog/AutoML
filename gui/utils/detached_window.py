# Author: Miguel Marina <karel.capek.robotics@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 Capek System Safety & Robotic Solutions
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Helpers for hosting detached diagrams in their own window."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .closable_notebook import ClosableNotebook, cancel_after_events
from .window_controls import restore_window_buttons
from .window_resizer import WindowResizeController


class DetachedWindow:
    """Create a floating window embedding a :class:`ClosableNotebook`.

    The window re-packs toolbars and toolboxes of the hosted widget and
    reactivates lifecycle hooks so the detached diagram behaves like it does
    within the main application.
    """

    def __init__(
        self, root: tk.Misc, width: int, height: int, x: int, y: int
    ) -> None:
        self.root = root
        self.win = tk.Toplevel(root)
        restore_window_buttons(self.win)
        self.win.geometry(f"{width}x{height}+{x}+{y}")
        self.nb = ClosableNotebook(self.win)
        self.nb.pack(expand=True, fill="both")
        self._resizer: WindowResizeController | None = None
        try:
            self._resizer = WindowResizeController(self.win, self.nb)
        except Exception:
            self._resizer = None
        self.win.bind("<Destroy>", self._on_destroy)

    # ------------------------------------------------------------------
    # Window setup helpers
    # ------------------------------------------------------------------
    def add(self, widget: tk.Widget, text: str) -> None:
        """Add *widget* to the notebook and run activation hooks."""
        self.nb.add(widget, text=text)
        self.add_moved_widget(widget, text)

    def add_moved_widget(self, widget: tk.Widget, text: str) -> None:
        """Accept an already-moved *widget* and trigger hooks."""
        try:
            self.nb.tab(widget, text=text)
        except Exception:
            pass
        self.nb.select(widget)
        if self._resizer is not None:
            self._resizer.add_target(widget)
        self._ensure_toolbox(widget)
        self._activate_hooks(widget)

    def _ensure_toolbox(self, widget: tk.Widget) -> None:
        """Ensure any toolbox frame is packed and functional."""
        frame = getattr(widget, "toolbox", getattr(widget, "tools_frame", None))
        if isinstance(frame, tk.Widget) and not frame.winfo_manager():
            try:
                frame.pack(side="left")
            except Exception:
                pass
        selector = getattr(widget, "toolbox_selector", None)
        switch = getattr(widget, "_switch_toolbox", None)
        if isinstance(selector, ttk.Combobox) and callable(switch):
            try:
                selector.bind("<<ComboboxSelected>>", lambda _e: switch())
            except Exception:
                pass

    def _activate_hooks(self, widget: tk.Widget) -> None:
        """Invoke lifecycle hooks on *widget* if present."""
        for name in ("_rebuild_toolboxes", "_activate_parent_phase", "_switch_toolbox"):
            func = getattr(widget, name, None)
            if callable(func):
                try:
                    func()
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def _on_destroy(self, _event: tk.Event) -> None:  # pragma: no cover - GUI event
        """Cancel pending callbacks when the window is destroyed."""
        try:
            cancel_after_events(self.win)
        except Exception:
            pass
        self._resizer = None
