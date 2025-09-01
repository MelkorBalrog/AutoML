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

"""Regression tests ensuring widgets persist after detachment."""

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


class TestWidgetRetention:
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

    def test_frames_remain(self) -> None:
        frames = [ttk.Frame(self.container) for _ in range(3)]
        for frm in frames:
            frm.pack()
        self.nb.update_idletasks()
        detached = _detach_notebook(self.nb)
        clones = [w for w in detached.winfo_children() if isinstance(w, ttk.Frame)]
        assert len(clones) == len(frames)

    def test_labels_remain(self) -> None:
        labels = [ttk.Label(self.container, text=str(i)) for i in range(4)]
        for lbl in labels:
            lbl.pack()
        self.nb.update_idletasks()
        detached = _detach_notebook(self.nb)
        clones = [w for w in detached.winfo_children() if isinstance(w, ttk.Label)]
        assert len(clones) == len(labels)

    def test_canvases_remain(self) -> None:
        canvases = [tk.Canvas(self.container, width=10, height=10) for _ in range(2)]
        for cvs in canvases:
            cvs.pack()
        self.nb.update_idletasks()
        detached = _detach_notebook(self.nb)
        clones = [w for w in detached.winfo_children() if isinstance(w, tk.Canvas)]
        assert len(clones) == len(canvases)

    def test_treeviews_remain(self) -> None:
        trees = [ttk.Treeview(self.container) for _ in range(2)]
        for tree in trees:
            tree.pack()
        self.nb.update_idletasks()
        detached = _detach_notebook(self.nb)
        clones = [w for w in detached.winfo_children() if isinstance(w, ttk.Treeview)]
        assert len(clones) == len(trees)

