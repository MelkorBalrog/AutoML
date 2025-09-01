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

"""Nested layout tests ensuring all widgets appear after detachment."""

import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


def _detach_notebook(nb: ClosableNotebook) -> ttk.Frame:
    class Event:  # simple namespace for event attributes
        ...

    press = Event()
    press.x = 5
    press.y = 5
    nb._on_tab_press(press)
    nb._dragging = True
    release = Event()
    release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
    release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
    nb._on_tab_release(release)
    assert nb._floating_windows, "Tab did not detach"
    float_nb = nb._floating_windows[0].winfo_children()[0]
    return float_nb.nametowidget(float_nb.tabs()[0])


class TestNestedLayoutVisibility:
    def setup_method(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        self.nb = ClosableNotebook(self.root)
        self.container = ttk.Frame(self.nb)
        self.nb.add(self.container, text="tab")

    def teardown_method(self) -> None:
        if hasattr(self, "root"):
            self.root.destroy()

    def test_all_widgets_visible(self) -> None:
        top = ttk.Frame(self.container)
        top.pack(side="top")
        lbl = ttk.Label(top, text="inner")
        lbl.pack(side="left")
        canvas = tk.Canvas(top, width=20, height=20)
        canvas.pack(side="right")

        bottom = ttk.Frame(self.container)
        bottom.pack(side="bottom", fill="both", expand=True)
        tree = ttk.Treeview(bottom)
        tree.grid(row=0, column=0, sticky="nsew")
        bottom.grid_rowconfigure(0, weight=1)
        bottom.grid_columnconfigure(0, weight=1)

        placed = ttk.Label(self.container, text="placed")
        placed.place(x=5, y=5)

        self.nb.update_idletasks()
        detached = _detach_notebook(self.nb)

        def descendants(widget: tk.Widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)

        clones = list(descendants(detached))
        assert any(isinstance(w, ttk.Frame) for w in clones), "Frame missing"
        assert any(isinstance(w, ttk.Label) and w.cget("text") == "inner" for w in clones), "Label missing"
        assert any(isinstance(w, tk.Canvas) for w in clones), "Canvas missing"
        assert any(isinstance(w, ttk.Treeview) for w in clones), "Treeview missing"
        assert any(isinstance(w, ttk.Label) and w.cget("text") == "placed" for w in clones), "Placed label missing"
