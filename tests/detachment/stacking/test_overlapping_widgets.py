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

"""Stacking behaviour tests for detached tabs."""

from __future__ import annotations

import os
import sys
import tkinter as tk
from tkinter import ttk
import pytest

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "gui", "utils"))
from closable_notebook import ClosableNotebook  # noqa: E402


WIDGET_FACTORIES = [
    ("label", lambda p: ttk.Label(p, text="lbl")),
    ("canvas", lambda p: tk.Canvas(p, width=20, height=20)),
    ("button", lambda p: ttk.Button(p, text="btn")),
]


class TestOverlappingStacking:
    """Grouped tests ensuring clones retain stacking order."""

    @pytest.mark.parametrize("_name,factory", WIDGET_FACTORIES, ids=[n for n, _ in WIDGET_FACTORIES])
    def test_overlapping_widget_visible_after_detach(self, _name, factory) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        container = tk.Frame(nb, width=100, height=100)
        nb.add(container, text="Tab1")

        bottom = tk.Frame(container, bg="red")
        bottom.place(x=0, y=0, relwidth=1, relheight=1)
        top = tk.Frame(container, bg="blue")
        top.place(x=0, y=0, relwidth=1, relheight=1)
        widget = factory(top)
        widget.pack()
        top.lift()
        nb.update_idletasks()

        class Event:
            ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        assert nb._floating_windows, "Tab did not detach"
        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_container = new_nb.nametowidget(new_nb.tabs()[0])
        new_top = next(c for c in new_container.winfo_children() if c.winfo_children())
        new_widget = new_top.winfo_children()[0]

        x = new_widget.winfo_rootx() + 1
        y = new_widget.winfo_rooty() + 1
        visible = win.winfo_containing(x, y)
        assert visible == new_widget
        root.destroy()
