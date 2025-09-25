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
from gui.utils.tk_utils import reparent_widget

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

    def test_float_reparents_into_container(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        nb.pack()
        frame = ttk.Frame(nb)
        nb.add(frame, text="T1")
        dw = DockableDiagramWindow(frame)

        nb.forget(frame)
        dw.float(300, 200, 10, 15, "Float Title")

        container = dw._float_container
        assert container is not None
        assert container.master is dw.win
        assert frame.master is container
        try:
            info = frame.pack_info()
        except tk.TclError:
            info = {}
        assert info.get("fill") == "both"
        assert info.get("expand") == "1"
        assert dw.win.winfo_viewable()
        assert dw.win.title() == "Float Title"

        dw.win.destroy()
        root.destroy()

    def test_dock_withdraws_floating_window(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        nb.pack()
        frame = ttk.Frame(nb)
        nb.add(frame, text="T1")
        dw = DockableDiagramWindow(frame)

        nb.forget(frame)
        dw.float(200, 200, 0, 0, "T1")
        dw.dock(nb, 0, "T1")

        state = "withdrawn"
        try:
            state = dw.win.state()
        except tk.TclError:
            pass
        assert state == "withdrawn"

        dw.win.destroy()
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

    def test_float_does_not_call_transient(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")

        frame = ttk.Frame(root)
        dw = DockableDiagramWindow(frame)

        called = {"transient": False}

        def fail_transient(self, *args, **kwargs):  # noqa: ANN001 - test helper
            called["transient"] = True
            raise AssertionError("DockableDiagramWindow should not mark the window transient")

        monkeypatch.setattr(tk.Toplevel, "transient", fail_transient)

        dw.float(200, 200, 0, 0, "Float Title")
        assert not called["transient"]
        if dw.toplevel is not None and dw.toplevel.winfo_exists():
            dw.toplevel.destroy()
        root.destroy()
        root.destroy()

    def test_win_creates_toplevel_once(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        frame = ttk.Frame(root)
        dw = DockableDiagramWindow(frame)
        win1 = dw.win
        assert isinstance(win1, tk.Toplevel)
        win2 = dw.win
        assert win1 is win2
        win1.destroy()
        root.destroy()
