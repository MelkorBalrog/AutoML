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

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from gui.utils.closable_notebook import ClosableNotebook


def test_tab_refresh_on_focus():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")

    nb = ClosableNotebook(root)

    class Tab(ttk.Frame):
        def __init__(self, master):
            super().__init__(master)
            self.refreshed = False
        def refresh_from_repository(self):
            self.refreshed = True

    tab1 = Tab(nb)
    tab2 = Tab(nb)
    nb.add(tab1, text="Tab1")
    nb.add(tab2, text="Tab2")
    nb.update_idletasks()

    # Switch to second tab then back to first to trigger refresh
    nb.select(nb.tabs()[1])
    tab1.refreshed = False
    nb.select(nb.tabs()[0])
    assert tab1.refreshed

    # Switch back to second tab and expect refresh
    tab2.refreshed = False
    nb.select(nb.tabs()[1])
    assert tab2.refreshed

    root.destroy()
