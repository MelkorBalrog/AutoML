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

"""Verify tab detachment and reattachment across toplevel windows."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.widget_transfer_manager import WidgetTransferManager


@pytest.mark.detachment
@pytest.mark.transfer
class TestTabTransferAcrossToplevel:
    """Grouped tests for moving tabs between separate toplevel windows."""

    def _setup_notebooks(self) -> tuple[tk.Tk, ClosableNotebook, ClosableNotebook, ttk.Frame, ttk.Label]:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb1 = ClosableNotebook(root)
        nb1.pack()
        frame = ttk.Frame(nb1)
        label = ttk.Label(frame, text="payload")
        label.pack()
        nb1.add(frame, text="Tab1")
        top = tk.Toplevel(root)
        nb2 = ClosableNotebook(top)
        nb2.pack()
        return root, nb1, nb2, frame, label

    def test_tab_moved_between_windows(self) -> None:
        root, nb1, nb2, frame, label = self._setup_notebooks()
        manager = WidgetTransferManager()
        tab_id = nb1.tabs()[0]
        moved = manager.detach_tab(nb1, tab_id, nb2)
        assert moved is not frame
        assert not frame.winfo_exists()
        assert nb2.nametowidget(nb2.tabs()[0]) is moved
        assert moved.nametowidget(label.winfo_name()) is label
        root.destroy()

    def test_detach_and_reattach(self) -> None:
        root, nb1, nb2, frame, label = self._setup_notebooks()
        manager = WidgetTransferManager()
        tab_id = nb1.tabs()[0]
        moved = manager.detach_tab(nb1, tab_id, nb2)
        back_id = nb2.tabs()[0]
        returned = manager.detach_tab(nb2, back_id, nb1)
        assert returned is not moved
        assert returned.master is nb1
        assert nb1.nametowidget(nb1.tabs()[0]) is returned
        assert returned.nametowidget(label.winfo_name()) is label
        root.destroy()

