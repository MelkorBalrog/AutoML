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
"""Tests for ``update_canvas_windows`` helper."""

import os
import tkinter as tk
import pytest

from closable_notebook import ClosableNotebook


class TestUpdateCanvasWindows:
    @pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
    def test_rewires_canvas_window_items(self):
        root = tk.Tk()
        nb = ClosableNotebook(root)
        canvas = tk.Canvas(nb)
        frame = tk.Frame(canvas)
        lst = tk.Listbox(frame)
        lst.insert("end", "item")
        lst.pack()
        canvas.create_window(0, 0, window=frame, anchor="nw")
        clone, mapping, layouts = nb._clone_widget(canvas, nb)
        nb.update_canvas_windows(mapping)
        item = clone.find_all()[0]
        win_path = clone.itemcget(item, "window")
        assert win_path
        clone_win = clone.nametowidget(win_path)
        assert isinstance(clone_win, tk.Frame)
        root.destroy()
