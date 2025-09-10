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


class DockableDiagramWindow:
    """Host a diagram so it can dock in a notebook or float in a window."""

    def __init__(self, content: ttk.Frame) -> None:
        self.content_frame = content
        self.toplevel: tk.Toplevel | None = None

    @property
    def win(self) -> tk.Toplevel:
        """Return the floating window, creating it on demand."""

        if self.toplevel is None:
            self.toplevel = tk.Toplevel()
            self.toplevel.withdraw()
        return self.toplevel

    # ------------------------------------------------------------------
    # Dock and float operations
    # ------------------------------------------------------------------
    def dock(self, notebook: ttk.Notebook, index: int, title: str) -> None:
        """Insert the diagram into *notebook* at *index*."""

        parent = self.content_frame.master
        if parent is not None:
            cancel_after_events(parent)
        cancel_after_events(self.content_frame)
        if parent is not notebook:
            reparent_widget(self.content_frame, notebook)
        tabs = notebook.tabs()
        if index >= len(tabs):
            notebook.add(self.content_frame, text=title)
        else:
            notebook.insert(index, self.content_frame, text=title)
        notebook.select(self.content_frame)

    def float(self, width: int, height: int, x: int, y: int, title: str) -> None:
        """Show the diagram in a separate transient window."""

        win = self.win
        if not hasattr(win, "notebook"):
            win.transient(self.content_frame.winfo_toplevel())
            nb = ttk.Notebook(win)
            nb.pack(expand=True, fill="both")
            win.notebook = nb  # type: ignore[attr-defined]
        else:
            nb = win.notebook  # type: ignore[attr-defined]

        parent = self.content_frame.master
        if parent is not None:
            cancel_after_events(parent)
        cancel_after_events(self.content_frame)
        if parent is not nb:
            reparent_widget(self.content_frame, nb)
        nb.add(self.content_frame, text=title)
        win.geometry(f"{width}x{height}+{x}+{y}")
        win.deiconify()
