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

"""State preservation tests for detached widgets."""

import os
import sys
import tkinter as tk
from tkinter import ttk
import pytest

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "gui", "controls"))
sys.path.append(os.path.join(root_dir, "gui", "utils"))
from capsule_button import CapsuleButton
from closable_notebook import ClosableNotebook


def _detach_setup(builder):
    """Create a notebook, run *builder* on its tab and detach it."""
    root = tk.Tk()
    nb = ClosableNotebook(root)
    frame = ttk.Frame(nb)
    widgets = builder(frame)
    nb.add(frame, text="T")
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

    win = nb._floating_windows[0]
    new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
    clone = new_nb.nametowidget(new_nb.tabs()[0])
    return root, clone, widgets


class TestWidgetStatePreservation:
    """Grouped tests verifying data cloning for common widgets."""

    def test_label_and_button_text_preserved(self) -> None:
        try:
            def builder(frame):
                lbl = ttk.Label(frame, text="LabelText")
                lbl.pack()
                btn = CapsuleButton(frame, text="ButtonText")
                btn.pack()
                return lbl, btn

            root, clone, (lbl, btn) = _detach_setup(builder)
        except tk.TclError:
            pytest.skip("Tk not available")
        cloned_label = next(w for w in clone.winfo_children() if isinstance(w, ttk.Label))
        cloned_button = next(w for w in clone.winfo_children() if isinstance(w, CapsuleButton))
        assert cloned_label.cget("text") == "LabelText"
        assert cloned_button._text == "ButtonText"
        root.destroy()

    def test_treeview_contents_preserved(self) -> None:
        try:
            def builder(frame):
                tree = ttk.Treeview(frame)
                tree.pack()
                a = tree.insert("", "end", text="A", values=(1,))
                tree.insert(a, "end", text="B", values=(2,))
                return tree

            root, clone, tree = _detach_setup(builder)
        except tk.TclError:
            pytest.skip("Tk not available")

        cloned_tree = next(w for w in clone.winfo_children() if isinstance(w, ttk.Treeview))

        def dump(tv, item=""):
            return [
                (tv.item(i, "text"), tv.item(i, "values"), dump(tv, i))
                for i in tv.get_children(item)
            ]

        assert dump(tree) == dump(cloned_tree)
        root.destroy()

    def test_canvas_contents_preserved(self) -> None:
        try:
            def builder(frame):
                cvs = tk.Canvas(frame, width=40, height=40)
                cvs.pack()
                cvs.create_rectangle(5, 5, 20, 20, fill="red")
                cvs.create_text(10, 30, text="Hi")
                return cvs

            root, clone, canvas = _detach_setup(builder)
        except tk.TclError:
            pytest.skip("Tk not available")

        cloned_canvas = next(w for w in clone.winfo_children() if isinstance(w, tk.Canvas))
        assert len(canvas.find_all()) == len(cloned_canvas.find_all())
        orig_types = [canvas.type(i) for i in canvas.find_all()]
        clone_types = [cloned_canvas.type(i) for i in cloned_canvas.find_all()]
        assert orig_types == clone_types
        root.destroy()

    def test_toolbox_button_preserved(self) -> None:
        try:
            def builder(frame):
                toolbox_canvas = tk.Canvas(frame, width=40, height=40)
                toolbox_canvas.pack()
                toolbox = ttk.Frame(toolbox_canvas)
                toolbox_canvas.create_window(0, 0, window=toolbox, anchor="nw")
                selector = ttk.Button(toolbox, text="Select")
                selector.pack()
                return selector

            root, clone, selector = _detach_setup(builder)
        except tk.TclError:
            pytest.skip("Tk not available")

        cloned_canvas = next(w for w in clone.winfo_children() if isinstance(w, tk.Canvas))
        win_id = cloned_canvas.find_all()[0]
        cloned_toolbox = cloned_canvas.itemcget(win_id, "window")
        # ``itemcget`` returns the Tcl name; ``nametowidget`` resolves it
        toolbox_widget = cloned_canvas.nametowidget(cloned_toolbox)
        cloned_selector = next(w for w in toolbox_widget.winfo_children() if isinstance(w, ttk.Button))
        assert cloned_selector.cget("text") == "Select"
        root.destroy()
