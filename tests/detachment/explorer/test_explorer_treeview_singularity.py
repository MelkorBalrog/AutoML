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

"""Ensure explorer detachment keeps a single treeview and icon column."""

from __future__ import annotations

import types
import tkinter as tk
from tkinter import ttk
import pytest

from gui.utils.closable_notebook import ClosableNotebook
from mainappsrc.core.open_windows_features import Open_Windows_Features


def _descendants(widget: tk.Widget):
    for child in widget.winfo_children():
        yield child
        yield from _descendants(child)


class DummyLifecycleUI:
    def __init__(self, nb: ClosableNotebook) -> None:
        self.nb = nb

    def _new_tab(self, title: str):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text=title)
        return frame


class TestExplorerTreeview:
    def test_open_single_treeview_and_icon(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")

        nb = ClosableNotebook(root)
        app = types.SimpleNamespace(
            doc_nb=nb,
            lifecycle_ui=DummyLifecycleUI(nb),
            safety_mgmt_toolbox=types.SimpleNamespace(
                modules=[], diagrams={}, list_diagrams=lambda: None
            ),
            refresh_all=lambda: None,
        )
        features = Open_Windows_Features(app)
        features.manage_safety_management()
        features.manage_safety_management()

        treeviews = [
            w for w in _descendants(app._safety_exp_tab) if isinstance(w, ttk.Treeview)
        ]
        assert len(treeviews) == 1
        assert not treeviews[0]["columns"]
        root.destroy()

    def test_detached_single_treeview_and_icon(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")

        nb = ClosableNotebook(root)
        app = types.SimpleNamespace(
            doc_nb=nb,
            lifecycle_ui=DummyLifecycleUI(nb),
            safety_mgmt_toolbox=types.SimpleNamespace(
                modules=[], diagrams={}, list_diagrams=lambda: None
            ),
            refresh_all=lambda: None,
        )
        features = Open_Windows_Features(app)
        features.manage_safety_management()

        tab_id = nb.tabs()[0]
        nb._detach_tab(tab_id, 50, 50)
        win = nb._floating_windows[0]
        nb2 = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        clone = nb2.nametowidget(nb2.tabs()[0])

        treeviews = [w for w in _descendants(clone) if isinstance(w, ttk.Treeview)]
        assert len(treeviews) == 1
        assert not treeviews[0]["columns"]
        win.destroy()
        root.destroy()
