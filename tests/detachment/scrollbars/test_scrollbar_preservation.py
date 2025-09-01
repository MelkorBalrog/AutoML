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

"""Scrollbar tests verifying view offsets persist after detachment."""

import os
import sys
import tkinter as tk
from tkinter import ttk
import pytest

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "gui", "utils"))
from closable_notebook import ClosableNotebook


def test_scrollbar_offset_preserved() -> None:
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    nb = ClosableNotebook(root)
    container = ttk.Frame(nb)
    canvas = tk.Canvas(container, width=100, height=100)
    vsb = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)
    canvas.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    nb.add(container, text="Canvas")
    canvas.create_rectangle(0, 0, 200, 400)
    canvas.yview_moveto(1.0)

    class Event: ...

    press = Event(); press.x = 5; press.y = 5
    nb._on_tab_press(press)
    nb._dragging = True
    release = Event()
    release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
    release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
    nb._on_tab_release(release)

    assert nb._floating_windows, "Tab did not detach"
    win = nb._floating_windows[-1]
    new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
    new_container = next(w for w in new_nb.winfo_children() if isinstance(w, ttk.Frame))
    new_canvas = next(w for w in new_container.winfo_children() if isinstance(w, tk.Canvas))
    assert new_canvas.yview()[0] > 0
    root.destroy()
