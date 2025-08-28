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

import os
import sys
import tkinter as tk
from tkinter import ttk
import pytest

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "gui", "utils"))
from closable_notebook import ClosableNotebook


class DummyDiagram(ttk.Frame):
    def __init__(self, master: tk.Widget):
        super().__init__(master)
        self.rebuilt = False
        self.fitted = False
        self.toolbox_canvas = tk.Canvas(self, width=40, height=40)
        self.toolbox_canvas.pack()
        self.toolbox = ttk.Frame(self.toolbox_canvas)
        self.toolbox_canvas.create_window(0, 0, window=self.toolbox, anchor="nw")
        self.clicks = 0
        self.btn = ttk.Button(self.toolbox, text="B", command=self._on_click)
        self.btn.pack()

    def _on_click(self) -> None:
        self.clicks += 1

    def _rebuild_toolboxes(self) -> None:
        self.rebuilt = True

    def _fit_toolbox(self) -> None:
        self.fitted = True


def test_toolbox_visible_and_functional_after_detach() -> None:
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")

    nb = ClosableNotebook(root)
    diagram = DummyDiagram(nb)
    nb.add(diagram, text="D")
    nb.update_idletasks()

    class Event:
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
    win = nb._floating_windows[0]
    new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
    clone = new_nb.nametowidget(new_nb.tabs()[0])

    assert clone.rebuilt is True
    assert clone.fitted is True

    btn = clone.btn
    x = btn.winfo_rootx() + 1
    y = btn.winfo_rooty() + 1
    visible = win.winfo_containing(x, y)
    assert visible == btn
    btn.invoke()
    assert clone.clicks == 1
    root.destroy()

