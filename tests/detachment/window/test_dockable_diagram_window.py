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

    def test_dock_cancels_parent_callbacks(self, monkeypatch: pytest.MonkeyPatch) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb_src = ClosableNotebook(root)
        nb_src.pack()
        nb_dst = ClosableNotebook(root)
        nb_dst.pack()
        frame = ttk.Frame(nb_src)
        nb_src.add(frame, text="T1")
        dw = DockableDiagramWindow(frame)

        called = {"parent": False, "child": False}

        def fake_cancel(widget, cancelled=None):  # noqa: ANN001 - test helper
            if widget is nb_src:
                called["parent"] = True
            if widget is frame:
                called["child"] = True

        monkeypatch.setattr(
            "gui.utils.dockable_diagram_window.cancel_after_events",
            fake_cancel,
        )

        dw.dock(nb_dst, 0, "T2")
        assert called["parent"] and called["child"]
        root.destroy()

    def test_float_cancels_parent_callbacks(self, monkeypatch: pytest.MonkeyPatch) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        nb.pack()
        frame = ttk.Frame(nb)
        nb.add(frame, text="T1")
        dw = DockableDiagramWindow(frame)

        called = {"parent": False, "child": False}

        def fake_cancel(widget, cancelled=None):  # noqa: ANN001 - test helper
            if widget is nb:
                called["parent"] = True
            if widget is frame:
                called["child"] = True

        monkeypatch.setattr(
            "gui.utils.dockable_diagram_window.cancel_after_events",
            fake_cancel,
        )

        dw.float(200, 200, 0, 0, "T1")
        assert called["parent"] and called["child"]
        if dw.toplevel is not None:
            dw.toplevel.destroy()
        root.destroy()
