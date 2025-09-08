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
"""Dock a diagram in a notebook or float it in a window."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .closable_notebook import ClosableNotebook
from .tk_utils import cancel_after_events, reparent_widget


class DockableDiagramWindow:
    """Allow a diagram to be docked into a notebook or floated."""

    def __init__(self, root: tk.Misc) -> None:
        self.root = root
        self.win = tk.Toplevel(root)
        self.win.transient(root)
        try:  # pragma: no cover - some platforms do not support grouping
            self.win.wm_group(root)
        except Exception:
            pass
        self.win.withdraw()
        self.content_frame = tk.Frame(self.win)
        self.content_frame.pack(expand=True, fill="both")
        self.win.bind("<Destroy>", self._on_destroy)
        self._notebook: ClosableNotebook | None = None

    # ------------------------------------------------------------------
    # Docking and floating
    # ------------------------------------------------------------------
    def dock(self, notebook: ClosableNotebook, index: int, title: str) -> None:
        """Insert the content into *notebook* at *index* with *title*."""
        self._notebook = notebook
        reparent_widget(self.content_frame, notebook)
        notebook.insert(index, self.content_frame, text=title)
        notebook.select(self.content_frame)
        self.win.withdraw()
        diagram = self._diagram()
        if diagram is not None:
            self._ensure_toolbox(diagram)
            self._activate_hooks(diagram)

    def float(self, x: int, y: int, width: int, height: int) -> None:
        """Withdraw the tab and display the diagram in a standalone window."""
        nb = self._notebook
        if nb is not None:
            try:
                nb.forget(self.content_frame)
            except Exception:
                pass
        reparent_widget(self.content_frame, self.win)
        self.content_frame.pack(expand=True, fill="both")
        self.win.geometry(f"{width}x{height}+{x}+{y}")
        self.win.deiconify()
        try:  # pragma: no cover - focus may fail on some setups
            self.win.focus_force()
        except tk.TclError:
            pass
        diagram = self._diagram()
        if diagram is not None:
            self._ensure_toolbox(diagram)
            self._activate_hooks(diagram)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _diagram(self) -> tk.Widget | None:
        children = self.content_frame.winfo_children()
        return children[0] if children else None

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
