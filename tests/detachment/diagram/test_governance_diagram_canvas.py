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

"""Regression tests for detached governance diagram canvases."""

import os
import sys
import tkinter as tk
import pytest

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "gui", "utils"))
from closable_notebook import ClosableNotebook


class TestGovernanceDiagramCanvas:
    def test_detached_canvas_retains_items_and_colors(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        canvas = tk.Canvas(nb, width=100, height=100)
        rect = canvas.create_rectangle(10, 10, 40, 40, fill="green", outline="blue", tags=("node",))
        clicked: list[tk.Event] = []

        def on_click(event: tk.Event) -> None:
            clicked.append(event)

        canvas.bind("<Button-1>", on_click)
        nb.add(canvas, text="Diag")
        nb.update_idletasks()

        class Event:
            pass

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
        canvases = [w for w in new_nb.winfo_children() if isinstance(w, tk.Canvas)]
        assert len(canvases) == 1, "Expected exactly one canvas in detached window"
        new_canvas = canvases[0]
        item = new_canvas.find_all()[0]
        assert new_canvas.itemcget(item, "fill") == "green"
        assert new_canvas.itemcget(item, "outline") == "blue"
        assert "node" in new_canvas.gettags(item)
        new_canvas.event_generate("<Button-1>", x=15, y=15)
        assert clicked, "Canvas binding lost after detachment"
        root.destroy()
