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

"""Regression tests for treeview cloning during tab detachment."""

import os
import sys
import tkinter as tk
from tkinter import ttk
import pytest

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "gui", "utils"))
from closable_notebook import ClosableNotebook


class TestTreeviewState:
    def test_icons_preserved_and_folders_open(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        tree = ttk.Treeview(nb)
        img = tk.PhotoImage(width=1, height=1)
        tree._img = img  # keep reference
        parent = tree.insert("", "end", text="p", image=img, open=True)
        tree.insert(parent, "end", text="c", image=img)
        nb.add(tree, text="Tree")
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
        win = nb._floating_windows[-1]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_tree = next(w for w in new_nb.winfo_children() if isinstance(w, ttk.Treeview))
        new_parent = new_tree.get_children("")[0]
        new_child = new_tree.get_children(new_parent)[0]
        assert new_tree.item(new_parent, "image"), "Parent icon missing"
        assert new_tree.item(new_child, "image"), "Child icon missing"
        assert new_tree.item(new_parent, "open"), "Folder collapsed"
        root.destroy()
