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


WIDGET_FACTORIES = [
    ("label", lambda p: ttk.Label(p, text="lbl")),
    ("entry", lambda p: ttk.Entry(p)),
    ("text", lambda p: tk.Text(p, width=10, height=2)),
    ("canvas", lambda p: tk.Canvas(p, width=20, height=20)),
    ("listbox", lambda p: tk.Listbox(p)),
    ("treeview", lambda p: ttk.Treeview(p)),
]


class TestWidgetVisibility:
    @pytest.mark.parametrize("_name,factory", WIDGET_FACTORIES, ids=[n for n, _ in WIDGET_FACTORIES])
    def test_widget_visible_after_detach(self, _name, factory) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        container = ttk.Frame(nb)
        nb.add(container, text="Tab1")
        widget = factory(container)
        widget.pack(expand=True)
        nb.update_idletasks()

        class Event:
            ...

        press = Event()
        press.x = 5
        press.y = 5
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

        def find_widget(parent: tk.Widget, cls: type[tk.Widget]) -> tk.Widget | None:
            for child in parent.winfo_children():
                if isinstance(child, cls):
                    return child
                found = find_widget(child, cls)
                if found is not None:
                    return found
            return None

        new_widget = find_widget(new_container, type(widget))
        assert new_widget is not None
        x = new_widget.winfo_rootx() + 1
        y = new_widget.winfo_rooty() + 1
        visible = win.winfo_containing(x, y)
        assert visible == new_widget
        root.destroy()
