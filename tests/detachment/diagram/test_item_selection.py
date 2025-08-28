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
"""Grouped tests ensuring diagram items remain selectable after detachment."""

import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


class TestDiagramSelection:
    """Verify canvas item bindings survive tab detachment."""

    def test_canvas_item_selection_after_detach(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        nb.pack(fill="both", expand=True)

        canvas = tk.Canvas(nb, width=50, height=50, background="white")
        nb.add(canvas, text="diag")

        selected: list[bool] = [False]

        rect = canvas.create_rectangle(5, 5, 20, 20, tags=("node",))
        canvas.tag_bind("node", "<Button-1>", lambda e: selected.__setitem__(0, True))

        nb._detach_tab(0, 0, 0)
        win = nb.floating_windows[0]
        detached_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        clone_canvas = next(w for w in detached_nb.winfo_children() if isinstance(w, tk.Canvas))

        clone_canvas.event_generate("<Button-1>", x=10, y=10)
        assert selected[0] is True

        win.destroy()
        root.destroy()
