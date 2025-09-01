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

"""Ensure explorer callbacks operate after detaching to a new window."""

from __future__ import annotations

import types
import tkinter as tk
import pytest

from gui.utils.closable_notebook import ClosableNotebook
import gui.explorers.safety_case_explorer as safety_case_explorer


class DummyTable:
    """Minimal stand-in for :class:`SafetyCaseTable`."""

    def __init__(self, master, case, app=None):
        self.master = master
        self.case = case
        self.packed = False

    def pack(self, **kwargs):
        self.packed = True


def test_open_callback_in_detached_window(monkeypatch):
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")

    case = types.SimpleNamespace(name="Case1", solutions=[], phase=None)
    library = types.SimpleNamespace(list_cases=lambda: [case], cases=[case])

    nb = ClosableNotebook(root)
    explorer = safety_case_explorer.SafetyCaseExplorer(nb, library=library)
    nb.add(explorer, text="Explorer")
    nb.update_idletasks()

    iid = explorer.tree.get_children("")[0]
    explorer.tree.selection_set(iid)

    called = {}

    class DummyTab(tk.Frame):
        def __init__(self, master):
            super().__init__(master)

        def pack(self, **kwargs):
            called["packed_tab"] = True

    def fake_new_tab(title):
        called["title"] = title
        return DummyTab(nb)

    explorer.app = types.SimpleNamespace(_new_tab=fake_new_tab)
    monkeypatch.setattr(safety_case_explorer, "SafetyCaseTable", DummyTable)

    tab_id = nb.tabs()[0]
    nb._detach_tab(tab_id, 50, 50)
    win = nb._floating_windows[0]
    nb2 = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
    clone = nb2.nametowidget(nb2.tabs()[0])

    iid2 = clone.tree.get_children("")[0]
    clone.tree.selection_set(iid2)
    clone.open_item()

    assert called["title"] == "Safety & Security Report: Case1"
    assert called.get("packed_tab") is True
    win.destroy()
    root.destroy()
