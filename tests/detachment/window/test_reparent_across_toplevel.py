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

"""Regression test for reparenting tabs across toplevel windows."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

import os

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.widget_transfer_manager import WidgetTransferManager


@pytest.mark.detachment
@pytest.mark.reparenting
class TestReparentAcrossToplevel:
    def test_widget_reparented_between_toplevels(self) -> None:
        if os.name != "nt":
            pytest.skip("OS-level reparenting implemented only on Windows")
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb1 = ClosableNotebook(root)
        nb1.pack()
        frame = ttk.Frame(nb1)
        nb1.add(frame, text="Tab1")
        top = tk.Toplevel(root)
        nb2 = ClosableNotebook(top)
        nb2.pack()
        tab_id = nb1.tabs()[0]
        manager = WidgetTransferManager()
        moved = manager.detach_tab(nb1, tab_id, nb2)
        assert moved is frame
        assert nb2.nametowidget(nb2.tabs()[0]) is frame
        assert frame.master is nb2
        root.destroy()
