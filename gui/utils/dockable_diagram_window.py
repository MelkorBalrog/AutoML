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

import typing as t

import tkinter as tk
from tkinter import ttk

from .tk_utils import cancel_after_events, reparent_widget
from .window_controls import restore_window_buttons
from .window_resizer import WindowResizeController


class DockableDiagramWindow:
    """Host a diagram so it can dock in a notebook or float in a window."""

    def __init__(self, content: tk.Widget) -> None:
        if isinstance(content, ttk.Notebook):
            content = ttk.Frame(content)
        self.content_frame = t.cast(tk.Widget, content)
        self.toplevel: tk.Toplevel | None = None
        self._float_container: ttk.Frame | None = None
        self._resizer: WindowResizeController | None = None
        self._notebook: ttk.Notebook | None = None

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
            try:
                self.toplevel.protocol("WM_DELETE_WINDOW", self._on_close)
            except Exception:
                pass
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

        self._cleanup_after_events()
        if self._resizer is not None:
            try:
                self._resizer.shutdown()
            except Exception:
                pass
        self.toplevel = None
        self._float_container = None
        self._resizer = None
        self._notebook = None

    def _cleanup_after_events(self) -> None:
        """Cancel outstanding ``after`` callbacks tied to floating widgets."""

        for widget in (self.content_frame, self.toplevel):
            if widget is None:
                continue
            try:
                cancel_after_events(widget)
            except Exception:
                continue

    def _on_close(self) -> None:
        """Handle user-initiated close requests for the floating window."""

        win = self.toplevel
        self._cleanup_after_events()
        if self._resizer is not None:
            try:
                self._resizer.shutdown()
            except Exception:
                pass
            self._resizer = None
        if win is not None:
            try:
                win.destroy()
            except tk.TclError:
                pass

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
        self._notebook = notebook

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
            self.content_frame.pack_configure(expand=True, fill="both")
        except tk.TclError:
            try:
                self.content_frame.pack(expand=True, fill="both")
            except tk.TclError:
                pass
        if self._resizer is not None:
            self._resizer.add_target(self.content_frame)

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
        self._notebook = None
