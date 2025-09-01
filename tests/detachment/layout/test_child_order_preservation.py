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
"""Regression tests for child order preservation when detaching tabs."""

import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


class TestChildOrderPreservation:
    """Grouped tests ensuring layout order remains unchanged."""

    def test_mixed_manager_order(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")

        nb = ClosableNotebook(root)
        nb.pack(fill="both", expand=True)

        frame = ttk.Frame(nb)
        nb.add(frame, text="mix")

        grid_widget = ttk.Label(frame, text="grid")
        grid_widget.grid(row=0, column=0)

        toolbox = ttk.Frame(frame, width=20, height=20)
        toolbox.pack(side="left")

        nb._detach_tab(0, 0, 0)
        win = nb.floating_windows[0]
        detached_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        clone = detached_nb.nametowidget(detached_nb.tabs()[0])

        children = clone.winfo_children()
        assert isinstance(children[0], ttk.Label)
        assert isinstance(children[1], ttk.Frame)
        assert children[1].pack_info().get("side") == "left"

        win.destroy()
        root.destroy()
