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

"""Tests for the dockable diagram window helper."""

from __future__ import annotations

import pytest
import tkinter as tk
from tkinter import ttk

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.dockable_diagram_window import DockableDiagramWindow


@pytest.mark.detachment
@pytest.mark.dockable
class TestDockableDiagramWindow:
    def test_dock_inserts_tab_into_empty_notebook(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        nb.pack()
        frame = ttk.Frame(root)
        dw = DockableDiagramWindow(frame)
        dw.dock(nb, 0, "A")
        assert nb.tabs()
        assert nb.nametowidget(nb.tabs()[0]) is frame
        root.destroy()

