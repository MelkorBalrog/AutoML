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

"""Verify widgets managed by ``grid`` survive tab detachment."""

import os
import sys
import tkinter as tk
from tkinter import ttk
import pytest

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "gui", "utils"))
from closable_notebook import ClosableNotebook


class TestGridWidgetsVisible:
    """Tests for cloning grid-managed children."""

    def test_grid_controls_visible_after_detach(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        container = ttk.Frame(nb)
        nb.add(container, text="Tab1")

        lbl = tk.Label(container, text="L")
        lbl.grid(row=0, column=0)
        btn = ttk.Button(container, text="B")
        btn.grid(row=0, column=1)
        tree = ttk.Treeview(container)
        tree.grid(row=1, column=0, columnspan=2)
        canvas = tk.Canvas(container, width=10, height=10)
        canvas.grid(row=2, column=0, columnspan=2)

        nb.update_idletasks()

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        assert nb._floating_windows, "Tab did not detach"
        win = nb._floating_windows[0]

        def walk(w):
            yield w
            for child in w.winfo_children():
                yield from walk(child)

        classes = {type(w).__name__ for w in walk(win)}
        assert {"Label", "Button", "Treeview", "Canvas"}.issubset(classes)
        root.destroy()
