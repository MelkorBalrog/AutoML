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
        try:
            self.win.grid_rowconfigure(0, weight=1)
            self.win.grid_columnconfigure(0, weight=1)
            self.nb.grid(row=0, column=0, sticky="nsew")
        except tk.TclError:
            # Fallback to ``pack`` when ``grid`` is unavailable on very old Tk
            # variants or when another geometry manager is already active.
            self.nb.pack(expand=True, fill="both")
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
        self._ensure_toolbox(widget)
        self._activate_hooks(widget)
        self._expand_widget(widget)

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

    def _expand_widget(self, widget: tk.Widget) -> None:
        """Force *widget* to stretch with the detached window."""

        manager = ""
        try:
            manager = widget.winfo_manager()
        except Exception:
            manager = ""

        if manager == "pack":
            self._expand_pack_widget(widget)
            return
        if manager == "grid":
            self._expand_grid_widget(widget)
            return
        if manager == "place":
            self._expand_place_widget(widget)
            return

        # Unknown or unmanaged widgets—try every strategy defensively.
        self._expand_pack_widget(widget)
        self._expand_grid_widget(widget)
        self._expand_place_widget(widget)

    def _expand_pack_widget(self, widget: tk.Widget) -> None:
        try:
            widget.pack_configure(expand=True, fill="both")
        except Exception:
            try:
                widget.pack(expand=True, fill="both")
            except Exception:
                pass

    def _expand_grid_widget(self, widget: tk.Widget) -> None:
        try:
            info = widget.grid_info()
        except Exception:
            info = {}

        sticky = info.get("sticky", "")
        desired = "nsew" if not sticky else "".join(sorted(set(sticky) | set("nsew")))
        if desired != sticky:
            try:
                widget.grid_configure(sticky=desired)
            except Exception:
                pass

        parent = getattr(widget, "master", None)
        if parent is None:
            return

        row = info.get("row")
        col = info.get("column")

        def _ensure_weight(configurator, index) -> None:
            if index is None:
                return
            try:
                idx = int(index)
            except Exception:
                return
            try:
                cfg = configurator(idx)
            except Exception:
                cfg = {}
            weight = 0
            if isinstance(cfg, dict):
                weight = cfg.get("weight", 0) or 0
            if weight:
                return
            try:
                configurator(idx, weight=1)
            except Exception:
                pass

        try:
            _ensure_weight(parent.grid_rowconfigure, row)
        except Exception:
            pass
        try:
            _ensure_weight(parent.grid_columnconfigure, col)
        except Exception:
            pass

    def _expand_place_widget(self, widget: tk.Widget) -> None:
        try:
            widget.place_configure(relx=0, rely=0, relwidth=1.0, relheight=1.0)
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
