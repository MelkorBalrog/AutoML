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

import os
import sys
import tkinter as tk
from tkinter import ttk
import pytest

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "gui", "utils"))
from closable_notebook import ClosableNotebook


class TestWidgetVisibility:
    def _detach_and_check(self, factory):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        container = ttk.Frame(nb)
        widget = factory(container)
        widget.pack()
        nb.add(container, text="Tab1")
        nb.update_idletasks()

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
        assert widget.winfo_ismapped(), "Widget became invisible after detachment"
        root.destroy()

    def test_frame_visible(self) -> None:
        def factory(parent: tk.Widget) -> tk.Widget:
            frame = ttk.Frame(parent)
            ttk.Label(frame, text="inner").pack()
            return frame

        self._detach_and_check(factory)

    def test_label_visible(self) -> None:
        self._detach_and_check(lambda parent: ttk.Label(parent, text="lbl"))

    def test_treeview_visible(self) -> None:
        def factory(parent: tk.Widget) -> tk.Widget:
            tree = ttk.Treeview(parent)
            tree.insert("", "end", text="item")
            return tree

        self._detach_and_check(factory)

    def test_canvas_visible(self) -> None:
        def factory(parent: tk.Widget) -> tk.Widget:
            canvas = tk.Canvas(parent, width=20, height=20)
            canvas.create_rectangle(0, 0, 10, 10, fill="blue")
            return canvas

        self._detach_and_check(factory)
