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

"""Dockable diagram window helper for fixed tabs."""

from __future__ import annotations

import typing as t

import tkinter as tk
from tkinter import ttk

from .tk_utils import cancel_after_events, reparent_widget


class DockableDiagramWindow:
    """Host a diagram that remains docked inside notebooks."""

    def __init__(self, content: tk.Widget) -> None:
        if isinstance(content, ttk.Notebook):
            content = ttk.Frame(content)
        self.content_frame = t.cast(tk.Widget, content)
        self._notebook: ttk.Notebook | None = None

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
        self._notebook = notebook

    def float(self, width: int, height: int, x: int, y: int, title: str) -> None:
        """Raise because floating tabs are disabled for safety."""

        raise RuntimeError(
            "Floating windows are disabled; tabs must remain docked in the notebook."
        )
