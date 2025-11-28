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

"""Tests for the dockable diagram window helper with fixed tabs."""

from __future__ import annotations

import pytest
import tkinter as tk
from tkinter import ttk

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.dockable_diagram_window import DockableDiagramWindow
from gui.utils.tk_utils import reparent_widget


@pytest.mark.detachment
@pytest.mark.dockable
class TestDockableDiagramWindow:
    def test_initialises_content_frame_for_notebook_parent(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        nb.pack()
        dw = DockableDiagramWindow(nb)
        assert dw.content_frame.master is nb
        assert not nb.tabs()
        root.destroy()

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

    def test_float_raises_runtime_error(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        frame = ttk.Frame(root)
        dw = DockableDiagramWindow(frame)
        with pytest.raises(RuntimeError):
            dw.float(200, 200, 0, 0, "Disabled")
        root.destroy()

    def test_dock_skips_reparent_when_parent_matches(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        nb.pack()
        frame = ttk.Frame(nb)
        nb.add(frame, text="T1")
        dw = DockableDiagramWindow(frame)

        called = False

        def fake_reparent(widget, new_parent):  # noqa: ANN001 - test helper
            nonlocal called
            called = True

        monkeypatch.setattr(
            "gui.utils.dockable_diagram_window.reparent_widget", fake_reparent
        )

        dw.dock(nb, 1, "T2")
        assert not called
        root.destroy()

    def test_reparent_widget_noop_when_parent_same(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        nb.pack()
        frame = ttk.Frame(nb)
        nb.add(frame, text="T1")
        reparent_widget(frame, nb)
        assert frame.master is nb
        root.destroy()

    def test_dock_updates_notebook_tracking(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        nb.pack()
        frame = ttk.Frame(root)
        dw = DockableDiagramWindow(frame)

        dw.dock(nb, 0, "Track")
        assert dw._notebook is nb
        assert nb.nametowidget(nb.tabs()[0]) is frame

        root.destroy()
