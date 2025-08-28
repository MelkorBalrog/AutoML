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
"""Verify diagram node selection after detaching tabs."""

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestDetachedDiagramNodeSelection:
    """Grouped tests for selecting nodes in detached diagrams."""

    def test_detached_canvas_tag_bindings_preserve_selection(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        canvas = tk.Canvas(nb, width=100, height=100)
        canvas.create_rectangle(10, 10, 30, 30, tags=("node",))
        clicked: list[tk.Event] = []

        def on_click(event: tk.Event) -> None:
            clicked.append(event)

        canvas.tag_bind("node", "<Button-1>", on_click)
        nb.add(canvas, text="Canvas")
        nb.update_idletasks()

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        win = nb._floating_windows[-1]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_canvas = next(w for w in new_nb.winfo_children() if isinstance(w, tk.Canvas))
        new_canvas.event_generate("<Button-1>", x=15, y=15)
        assert clicked, "Node selection binding lost after detachment"
        root.destroy()
