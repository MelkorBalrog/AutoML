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

"""Regression tests for stacked widget detachment."""

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


class TestStackingRegression:
    """Grouped regression tests ensuring widgets remain visible."""

    def _build_overlapping(self, nb: ClosableNotebook) -> tk.Frame:
        container = tk.Frame(nb, width=100, height=100)
        nb.add(container, text="Tab1")
        bottom = tk.Frame(container, bg="red")
        bottom.place(x=0, y=0, relwidth=1, relheight=1)
        top = tk.Frame(container, bg="blue")
        top.place(x=0, y=0, relwidth=1, relheight=1)
        ttk.Label(top, text="lbl").pack()
        ttk.Button(top, text="btn").pack()
        top.lift()
        nb.update_idletasks()
        return container

    def _detach(self, nb: ClosableNotebook) -> tk.Toplevel:
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
        return nb._floating_windows[0]

    def test_no_tclerror_on_detach(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        self._build_overlapping(nb)
        try:
            self._detach(nb)
        except tk.TclError as exc:
            root.destroy()
            pytest.fail(f"TclError raised: {exc}")
        root.destroy()

    def test_all_widgets_visible_after_detach(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        self._build_overlapping(nb)
        win = self._detach(nb)
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        container = new_nb.nametowidget(new_nb.tabs()[0])
        top = next(c for c in container.winfo_children() if c.winfo_children())
        for widget in top.winfo_children():
            x = widget.winfo_rootx() + 1
            y = widget.winfo_rooty() + 1
            visible = win.winfo_containing(x, y)
            assert visible == widget
        root.destroy()
