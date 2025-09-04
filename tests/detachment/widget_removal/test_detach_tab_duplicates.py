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

"""Tests ensuring detachment removes duplicate widgets."""

import os
import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestDetachTabDuplicateCleanup:
    """Grouped tests for detachment duplicate cleanup."""

    def test_detach_tab_removes_first_and_fourth(self):
        root = tk.Tk()
        root.withdraw()
        nb = ClosableNotebook(root)
        tab = tk.Frame(nb)
        nb.add(tab, text="T")
        widgets = [tk.Label(tab, text=c) for c in "ABCD"]
        for w in widgets:
            w.pack()
        nb._detach_tab(nb.tabs()[0], 0, 0)
        toplevel = nb._floating_windows[-1]
        nb_detached = next(
            child for child in toplevel.winfo_children() if isinstance(child, ttk.Notebook)
        )
        cloned_tab = nb_detached.nametowidget(nb_detached.tabs()[0])
        texts = [child.cget("text") for child in cloned_tab.winfo_children()]
        assert texts == ["B", "C"]
        for child in cloned_tab.winfo_children():
            assert child.winfo_manager() == "pack"
            assert child in cloned_tab.winfo_children()
        toplevel.destroy()
        root.destroy()
