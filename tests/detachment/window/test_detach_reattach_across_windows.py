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

"""Tests for detaching and reattaching tabs across windows."""

from __future__ import annotations

import pytest
import tkinter as tk
from tkinter import ttk

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.widget_transfer_manager import WidgetTransferManager
import gui.utils.widget_transfer_manager as wtm


@pytest.mark.detachment
@pytest.mark.reparenting
class TestDetachReattachAcrossWindows:
    def test_detach_and_reattach_between_windows(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb1 = ClosableNotebook(root)
        nb1.pack()
        frame = ttk.Frame(nb1)
        lbl = ttk.Label(frame, text="hi")
        lbl.pack()
        nb1.add(frame, text="Tab1")

        top = tk.Toplevel(root)
        nb2 = ClosableNotebook(top)
        nb2.pack()
        manager = WidgetTransferManager()

        tab_id = nb1.tabs()[0]
        moved = manager.detach_tab(nb1, tab_id, nb2)
        assert lbl.winfo_exists()
        assert lbl.master is moved
        assert moved is frame
        assert nb2.nametowidget(nb2.tabs()[0]) is frame

        tab_id2 = nb2.tabs()[0]
        moved_back = manager.detach_tab(nb2, tab_id2, nb1)
        assert lbl.master is moved_back
        assert moved_back is frame
        assert nb1.nametowidget(nb1.tabs()[0]) is frame
        root.destroy()

    def test_tab_registered_before_reparent(self, monkeypatch) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb1 = ClosableNotebook(root)
        nb1.pack()
        frame = ttk.Frame(nb1)
        nb1.add(frame, text="T1")

        top = tk.Toplevel(root)
        nb2 = ClosableNotebook(top)
        nb2.pack()
        manager = WidgetTransferManager()

        call_order: list[str] = []
        registered: list[tk.Widget] = []

        def fake_add(child, **kw):
            call_order.append("add")
            registered.append(child)

        def fake_select(child):
            pass

        def fake_tabs():
            return [str(w) for w in registered]

        monkeypatch.setattr(nb2, "add", fake_add)
        monkeypatch.setattr(nb2, "select", fake_select)
        monkeypatch.setattr(nb2, "tabs", fake_tabs)

        def spy_reparent(child, new_parent):
            call_order.append("reparent")
            assert registered

        monkeypatch.setattr(wtm, "reparent_widget", spy_reparent)

        tab_id = nb1.tabs()[0]
        manager.detach_tab(nb1, tab_id, nb2)
        assert call_order == ["add", "reparent"]
        root.destroy()
