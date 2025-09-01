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


class TestWidgetStackOrder:
    def test_overlapping_widgets_visible_after_detach(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        container = tk.Frame(nb, width=100, height=100)
        nb.add(container, text="Tab1")

        bottom = tk.Frame(container, bg="red")
        bottom.place(x=0, y=0, relwidth=1, relheight=1)
        top = tk.Frame(container, bg="blue")
        top.place(x=0, y=0, relwidth=1, relheight=1)
        lbl = ttk.Label(top, text="top")
        lbl.pack()
        top.lift()
        nb.update_idletasks()

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        assert nb._floating_windows, "Tab did not detach"
        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_container = new_nb.nametowidget(new_nb.tabs()[0])
        frames = [c for c in new_container.winfo_children() if isinstance(c, tk.Frame)]
        new_top = next(f for f in frames if f.winfo_children())
        new_label = new_top.winfo_children()[0]

        x = new_label.winfo_rootx() + 1
        y = new_label.winfo_rooty() + 1
        visible = win.winfo_containing(x, y)
        assert visible == new_label
        root.destroy()

    def test_canvas_visible_after_detach(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        container = tk.Frame(nb, width=100, height=100)
        nb.add(container, text="Tab1")

        bottom = tk.Frame(container, bg="red")
        bottom.place(x=0, y=0, relwidth=1, relheight=1)
        canvas = tk.Canvas(container, bg="blue")
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        canvas.create_rectangle(0, 0, 10, 10, fill="blue")
        canvas.lift()
        nb.update_idletasks()

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        assert nb._floating_windows, "Tab did not detach"
        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_container = new_nb.nametowidget(new_nb.tabs()[0])
        new_canvas = next(c for c in new_container.winfo_children() if isinstance(c, tk.Canvas))

        x = new_canvas.winfo_rootx() + 1
        y = new_canvas.winfo_rooty() + 1
        visible = win.winfo_containing(x, y)
        assert visible == new_canvas
        root.destroy()

    def test_toolbox_visible_after_detach(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        container = tk.Frame(nb, width=100, height=100)
        nb.add(container, text="Tab1")

        bottom = tk.Frame(container, bg="red")
        bottom.place(x=0, y=0, relwidth=1, relheight=1)
        toolbox_canvas = tk.Canvas(container, width=40, height=40)
        toolbox_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        toolbox = ttk.Frame(toolbox_canvas)
        toolbox_canvas.create_window(0, 0, window=toolbox, anchor="nw")
        button = ttk.Button(toolbox, text="B")
        button.pack()
        toolbox_canvas.lift()
        nb.update_idletasks()

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        assert nb._floating_windows, "Tab did not detach"
        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_container = new_nb.nametowidget(new_nb.tabs()[0])
        new_tool_canvas = next(c for c in new_container.winfo_children() if isinstance(c, tk.Canvas))
        new_button = next(b for b in new_tool_canvas.winfo_children() if isinstance(b, ttk.Button))

        x = new_button.winfo_rootx() + 1
        y = new_button.winfo_rooty() + 1
        visible = win.winfo_containing(x, y)
        assert visible == new_button
        root.destroy()
