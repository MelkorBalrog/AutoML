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

"""Dockable diagram window helper."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .tk_utils import cancel_after_events, reparent_widget
from .window_controls import restore_window_buttons
from .window_resizer import WindowResizeController


class DockableDiagramWindow:
    """Host a diagram so it can dock in a notebook or float in a window."""

    def __init__(self, content: ttk.Frame) -> None:
        self.content_frame = content
        self.toplevel: tk.Toplevel | None = None
        self._float_container: ttk.Frame | None = None
        self._resizer: WindowResizeController | None = None

    @property
    def win(self) -> tk.Toplevel:
        """Return the floating window, creating it on demand."""

        if self.toplevel is None or not self.toplevel.winfo_exists():
            self.toplevel = tk.Toplevel()
            self.toplevel.withdraw()
            restore_window_buttons(self.toplevel)
            self._float_container = None
            try:
                self._resizer = WindowResizeController(self.toplevel)
            except Exception:
                self._resizer = None
            self.toplevel.bind("<Destroy>", self._on_destroy, add="+")
        return self.toplevel

    def _ensure_float_container(self, win: tk.Toplevel) -> ttk.Frame:
        """Return the floating container, creating it when necessary."""

        container = self._float_container
        if container is None or not container.winfo_exists():
            container = ttk.Frame(win)
            container.pack(expand=True, fill="both")
            self._float_container = container
        if self._resizer is not None:
            self._resizer.set_primary_target(container)
        return container

    def _release_from_geometry(self) -> None:
        """Release the content frame from any existing geometry manager."""

        parent = self.content_frame.master
        if isinstance(parent, ttk.Notebook):
            try:
                parent.forget(self.content_frame)
            except tk.TclError:
                pass

        try:
            manager = self.content_frame.winfo_manager()
        except Exception:
            return

        try:
            if manager == "pack":
                self.content_frame.pack_forget()
            elif manager == "grid":
                self.content_frame.grid_forget()
            elif manager == "place":
                self.content_frame.place_forget()
        except tk.TclError:
            pass

    def _on_destroy(self, _event: tk.Event) -> None:
        """Reset cached handles when the floating window is destroyed."""

        self.toplevel = None
        self._float_container = None
        self._resizer = None

    # ------------------------------------------------------------------
    # Dock and float operations
    # ------------------------------------------------------------------
    def dock(self, notebook: ttk.Notebook, index: int, title: str) -> None:
        """Insert the diagram into *notebook* at *index*."""

        parent = self.content_frame.master
        if parent is not None:
            cancel_after_events(parent)
        cancel_after_events(self.content_frame)
        self._release_from_geometry()
        if parent is not notebook:
            reparent_widget(self.content_frame, notebook)
        tabs = notebook.tabs()
        if index >= len(tabs):
            notebook.add(self.content_frame, text=title)
        else:
            notebook.insert(index, self.content_frame, text=title)
        notebook.select(self.content_frame)
        if self.toplevel is not None and self.toplevel.winfo_exists():
            try:
                self.toplevel.withdraw()
            except tk.TclError:
                pass
        if self._resizer is not None:
            self._resizer.remove_target(self.content_frame)

    def float(self, width: int, height: int, x: int, y: int, title: str) -> None:
        """Show the diagram in a separate top-level window."""

        win = self.win
        restore_window_buttons(win)

        container = self._ensure_float_container(win)

        parent = self.content_frame.master
        if parent is not None:
            cancel_after_events(parent)
        cancel_after_events(self.content_frame)
        self._release_from_geometry()
        if parent is not container:
            reparent_widget(self.content_frame, container)

        try:
            self.content_frame.pack(in_=container, expand=True, fill="both")
        except tk.TclError:
            try:
                self.content_frame.pack_configure(
                    in_=container, expand=True, fill="both"
                )
            except tk.TclError:
                try:
                    self.content_frame.pack_configure(expand=True, fill="both")
                except tk.TclError:
                    pass

        try:
            win.title(title)
        except tk.TclError:
            pass
        win.geometry(f"{width}x{height}+{x}+{y}")
        win.deiconify()
        try:
            win.lift()
        except tk.TclError:
            pass
