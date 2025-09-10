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
"""Tests for detaching tabs with ``DockableDiagramWindow``."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import pytest

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.dockable_diagram_window import DockableDiagramWindow


@pytest.mark.detachment
@pytest.mark.dockable
class TestClosableNotebookDockable:
    def test_detach_uses_dock_window_toplevel(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        nb.pack()
        frame = ttk.Frame(nb)
        dock = DockableDiagramWindow(frame)
        frame._dock_window = dock
        nb.add(frame, text="T1")
        tab_id = nb.tabs()[0]
        nb._detach_tab(tab_id, 10, 10)
        assert dock.toplevel in nb._floating_windows
        if dock.toplevel is not None:
            dock.toplevel.destroy()
        root.destroy()
