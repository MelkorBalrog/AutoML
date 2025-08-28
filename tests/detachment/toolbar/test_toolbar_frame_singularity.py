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

"""Grouped tests ensuring detached windows contain a single toolbar frame."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


def _detach_with_toolbar() -> tuple[tk.Tk, tk.Toplevel]:
    """Detach a tab containing a toolbar and return root and detached window."""

    root = tk.Tk()
    nb = ClosableNotebook(root)
    frame = tk.Frame(nb)
    nb.add(frame, text="T")
    toolbar = tk.Frame(frame)
    toolbar.pack()
    ttk.Button(toolbar, text="B").pack()
    nb.update_idletasks()
    nb._detach_tab(nb.tabs()[0], 40, 40)
    win = nb._floating_windows[0]
    return root, win


class TestToolbarFrameSingularity:
    """Grouped case verifying toolbar frame uniqueness after detachment."""

    def test_single_toolbar_frame(self) -> None:
        try:
            root, win = _detach_with_toolbar()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        frame = nb.nametowidget(nb.tabs()[0])
        toolbars = [
            child
            for child in frame.winfo_children()
            if isinstance(child, tk.Frame)
            and any(isinstance(gc, (tk.Button, ttk.Button)) for gc in child.winfo_children())
        ]
        assert len(toolbars) == 1
        win.destroy()
        root.destroy()
