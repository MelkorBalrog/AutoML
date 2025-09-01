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

import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


def test_mixed_geometry_children_visible() -> None:
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    nb = ClosableNotebook(root)
    nb.pack(fill="both", expand=True)

    frame = ttk.Frame(nb)
    nb.add(frame, text="mix")

    # grid-managed label
    label = ttk.Label(frame, text="Label")
    label.grid(row=0, column=0)

    # pack-managed button
    button = ttk.Button(frame, text="Button")
    button.pack(side="left")

    # place-managed canvas
    canvas = tk.Canvas(frame, width=50, height=20)
    canvas.place(x=10, y=30)

    nb._detach_tab(0, 0, 0)
    win = nb.floating_windows[0]

    names = {child.winfo_class() for child in win.winfo_children()}
    assert {"TLabel", "TButton", "Canvas"} <= names

    win.destroy()
    root.destroy()
