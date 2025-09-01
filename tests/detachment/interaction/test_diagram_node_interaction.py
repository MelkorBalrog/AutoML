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
"""Verify diagram node interaction after detaching tabs."""

import os
import tkinter as tk

import pytest

from gui.utils import drawing_helper
from gui.utils.closable_notebook import ClosableNotebook


class DummyApp:
    """Minimal application providing canvas interaction callbacks."""

    def __init__(self, canvas: tk.Canvas) -> None:
        self.canvas = canvas
        self.clicked: list[tuple[int, int]] = []
        self._last: tuple[int, int] = (0, 0)

    def on_canvas_click(self, event: tk.Event) -> None:
        self.clicked.append((event.x, event.y))
        self._last = (event.x, event.y)

    def on_canvas_drag(self, event: tk.Event) -> None:
        dx = event.x - self._last[0]
        dy = event.y - self._last[1]
        self.canvas.move("node", dx, dy)
        self._last = (event.x, event.y)

    def on_canvas_release(self, _e: tk.Event) -> None: ...

    def on_canvas_double_click(self, _e: tk.Event) -> None: ...

    def on_ctrl_mousewheel(self, _e: tk.Event) -> None: ...

    def on_right_mouse_press(self, _e: tk.Event) -> None: ...

    def on_right_mouse_drag(self, _e: tk.Event) -> None: ...

    def on_right_mouse_release(self, _e: tk.Event) -> None: ...


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestDetachedDiagramNodeInteraction:
    """Grouped tests for diagram node selection and movement."""

    def _detach(self) -> tuple[tk.Tk, ClosableNotebook, tk.Canvas, DummyApp]:
        root = tk.Tk()
        nb = ClosableNotebook(root)
        canvas = tk.Canvas(nb, width=100, height=100)
        canvas.create_rectangle(10, 10, 30, 30, tags=("node",))
        app = DummyApp(canvas)
        drawing_helper.init_diagram_canvas(canvas, app)
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
        return root, new_nb, new_canvas, app

    def test_detached_canvas_bindings_preserve_selection(self) -> None:
        try:
            root, _nb, canvas, app = self._detach()
        except tk.TclError:
            pytest.skip("Tk not available")
        canvas.event_generate("<Button-1>", x=15, y=15)
        assert app.clicked, "Node selection binding lost after detachment"
        root.destroy()

    def test_detached_canvas_bindings_preserve_drag(self) -> None:
        try:
            root, _nb, canvas, app = self._detach()
        except tk.TclError:
            pytest.skip("Tk not available")
        canvas.event_generate("<Button-1>", x=15, y=15)
        canvas.event_generate("<B1-Motion>", x=25, y=25)
        coords = list(map(int, canvas.coords("node")))
        assert coords == [20, 20, 40, 40], "Node movement binding lost after detachment"
        root.destroy()
