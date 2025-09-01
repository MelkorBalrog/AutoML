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
"""Regression tests for canvases containing nested frames and controls."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestCanvasWindowItemDetachment:
    def _detach(self, nb: ClosableNotebook) -> tk.Widget:
        class Event:
            pass

        press = Event()
        press.x = 5
        press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)
        win = nb._floating_windows[-1]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        return next(iter(new_nb.winfo_children()))

    def test_nested_frames_and_controls_survive_detachment(self) -> None:
        root = tk.Tk()
        nb = ClosableNotebook(root)
        container = tk.Frame(nb)
        canvas = tk.Canvas(container, width=100, height=100)
        inner = tk.Frame(canvas)
        label = tk.Label(inner, text="Label")
        button = tk.Button(inner, text="Button")
        label.pack()
        button.pack()
        canvas.create_window(10, 10, window=inner, anchor="nw")
        canvas.pack()
        nb.add(container, text="Canvas")
        nb.update_idletasks()
        clone = self._detach(nb)
        clone_canvas = next(c for c in clone.winfo_children() if isinstance(c, tk.Canvas))
        cloned_inner = clone_canvas.winfo_children()[0]
        cloned_label = next(w for w in cloned_inner.winfo_children() if isinstance(w, tk.Label))
        cloned_button = next(w for w in cloned_inner.winfo_children() if isinstance(w, tk.Button))
        assert cloned_label.cget("text") == "Label"
        assert cloned_button.cget("text") == "Button"
        root.destroy()
