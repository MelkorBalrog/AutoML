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
import pytest
import tkinter as tk
from tkinter import ttk

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)
from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.detachment
@pytest.mark.reparenting
class TestDetachmentReparenting:
    def test_standard_widget_moved_not_cloned(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb1 = ClosableNotebook(root)
        nb1.pack()
        label = ttk.Label(nb1, text="hello")
        nb1.add(label, text="L1")
        nb2 = ClosableNotebook(root)
        nb2.pack()
        tab_id = nb1.tabs()[0]
        assert nb1._move_tab(tab_id, nb2)
        assert nb2.nametowidget(nb2.tabs()[0]) is label
        root.destroy()

    def test_layout_preserved_during_move(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb1 = ClosableNotebook(root)
        nb1.pack()
        nb2 = ClosableNotebook(root)
        nb2.pack()
        tab = ttk.Frame(nb1)
        lbl_pack = ttk.Label(tab, text="pack")
        lbl_pack.pack(side="left")
        grid_container = ttk.Frame(tab)
        grid_container.pack(side="left")
        lbl_grid = ttk.Label(grid_container, text="grid")
        lbl_grid.grid(row=0, column=0, padx=5)
        nb1.add(tab, text="T")
        pack_before = lbl_pack.pack_info()
        grid_before = lbl_grid.grid_info()
        tab_id = nb1.tabs()[0]
        assert nb1._move_tab(tab_id, nb2)
        assert lbl_pack.pack_info()["side"] == pack_before["side"]
        assert lbl_grid.grid_info()["row"] == grid_before["row"]
        assert lbl_grid.grid_info()["column"] == grid_before["column"]
        root.destroy()
