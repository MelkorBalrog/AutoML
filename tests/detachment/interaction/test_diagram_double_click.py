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

"""Tests for double-click interactions on detached diagram canvases."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestDetachedDiagramDoubleClick:
    """Grouped tests verifying diagram item callbacks after detachment."""

    def _detach(self, nb: ClosableNotebook) -> tuple[tk.Canvas, tk.Tk]:
        class Event: ...

        press = Event()
        press.x = 5
        press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True

        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        win = nb._floating_windows[0]
        new_nb = next(
            w for w in win.winfo_children() if isinstance(w, ClosableNotebook)
        )
        clone = new_nb.nametowidget(new_nb.tabs()[0])
        return clone, win

    def test_double_click_triggers_callback_after_detach(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        root.withdraw()

        nb = ClosableNotebook(root)
        canvas = tk.Canvas(nb, width=100, height=100)
        canvas.create_rectangle(10, 10, 90, 90, tags=("node",))
        hits: list[str] = []
        canvas.tag_bind("node", "<Double-1>", lambda e: hits.append("node"))
        nb.add(canvas, text="Tab1")
        nb.update_idletasks()

        clone, win = self._detach(nb)
        clone.event_generate("<Double-1>", x=50, y=50)
        win.update()

        assert hits == ["node"]
        root.destroy()

    def test_multiple_tag_double_clicks_trigger_callbacks_after_detach(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        root.withdraw()

        nb = ClosableNotebook(root)
        canvas = tk.Canvas(nb, width=100, height=100)
        canvas.create_rectangle(10, 10, 90, 90, tags=("node", "parent"))
        hits: list[str] = []
        canvas.tag_bind("node", "<Double-1>", lambda e: hits.append("node"))
        canvas.tag_bind("parent", "<Double-1>", lambda e: hits.append("parent"))
        nb.add(canvas, text="Tab1")
        nb.update_idletasks()

        clone, win = self._detach(nb)
        clone.event_generate("<Double-1>", x=50, y=50)
        win.update()

        assert hits == ["node", "parent"]
        root.destroy()

