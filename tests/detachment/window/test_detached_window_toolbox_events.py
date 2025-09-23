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
"""Tests for the :class:`DetachedWindow` utility."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.detached_window import DetachedWindow


class DummyDiagram(tk.Frame):
    """Minimal diagram stub exposing a toolbox and hooks."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.log: list[str] = []
        self.toolbox = tk.Frame(self)
        tk.Button(self.toolbox, text="B", command=lambda: self.log.append("btn")).pack()
        self.toolbox.pack(side="left")
        self.toolbox_selector = ttk.Combobox(self, values=["A", "B"])
        self.toolbox_selector.pack()

    def _rebuild_toolboxes(self) -> None:  # pragma: no cover - trivial
        self.log.append("rebuild")

    def _activate_parent_phase(self) -> None:  # pragma: no cover - trivial
        self.log.append("activate")

    def _switch_toolbox(self) -> None:  # pragma: no cover - trivial
        self.log.append("switch")


class TestDetachedWindowToolboxes:
    def test_toolbox_exposed_and_button_active(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        diagram = DummyDiagram(root)
        diagram.toolbox.pack_forget()
        win = DetachedWindow(root, width=200, height=200, x=10, y=10)
        win.add(diagram, "Tab")
        assert diagram.log[:3] == ["rebuild", "activate", "switch"]
        assert diagram.toolbox.winfo_manager() == "pack"
        btn = diagram.toolbox.winfo_children()[0]
        btn.invoke()
        assert diagram.log[-1] == "btn"
        root.destroy()


class TestDetachedWindowWidgetEvents:
    def test_selector_event_triggers_switch(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        diagram = DummyDiagram(root)
        diagram.toolbox.pack_forget()
        win = DetachedWindow(root, width=200, height=200, x=10, y=10)
        win.add(diagram, "Tab")
        count = diagram.log.count("switch")
        diagram.toolbox_selector.event_generate("<<ComboboxSelected>>")
        assert diagram.log.count("switch") == count + 1
        root.destroy()


class TestDetachedWindowWindowControls:
    def test_detached_window_does_not_use_transient(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")

        called = {"transient": False}

        def fail_transient(self, *args, **kwargs):  # noqa: ANN001 - test helper
            called["transient"] = True
            raise AssertionError("DetachedWindow should not mark the window transient")

        monkeypatch.setattr(tk.Toplevel, "transient", fail_transient)

        win = DetachedWindow(root, width=200, height=200, x=10, y=10)
        assert not called["transient"]
        win.win.destroy()
        root.destroy()


class TestDetachedWindowResizing:
    def test_detached_tab_expands_with_window(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")

        win = DetachedWindow(root, width=200, height=200, x=20, y=20)
        frame = tk.Frame(win.nb)
        canvas = tk.Canvas(frame, width=50, height=50)
        canvas.pack()
        win.add(frame, "Tab")

        win.win.update_idletasks()
        manager = frame.winfo_manager()

        if manager == "pack":
            info = frame.pack_info()
            assert info.get("expand") == "1"
            assert info.get("fill") == "both"
        elif manager == "grid":
            info = frame.grid_info()
            sticky = info.get("sticky", "")
            assert set("nsew").issubset(set(sticky))
            parent = frame.master
            row = int(info.get("row", 0))
            col = int(info.get("column", 0))
            assert parent.grid_rowconfigure(row).get("weight", 0) > 0
            assert parent.grid_columnconfigure(col).get("weight", 0) > 0
        elif manager == "place":
            info = frame.place_info()
            assert info.get("relwidth") == "1.0"
            assert info.get("relheight") == "1.0"
        else:  # pragma: no cover - unexpected geometry manager
            pytest.skip(f"Unhandled geometry manager: {manager}")

        win.win.geometry("460x420")
        win.win.update_idletasks()
        assert frame.winfo_width() == win.nb.winfo_width()
        assert frame.winfo_height() == win.nb.winfo_height()
        root.destroy()

    def test_notebook_detach_expands_with_floating_window(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")

        nb = ClosableNotebook(root)
        nb.pack(expand=True, fill="both")
        frame = tk.Frame(nb)
        canvas = tk.Canvas(frame, width=60, height=60)
        canvas.pack(expand=True, fill="both")
        nb.add(frame, text="Tab")
        nb.update_idletasks()

        tab_id = nb.tabs()[0]
        nb._detach_tab(tab_id, x=30, y=30)

        assert nb._floating_windows, "Detachment did not create a floating window"
        win = nb._floating_windows[-1]
        floating_nb = next(
            child for child in win.winfo_children() if isinstance(child, ClosableNotebook)
        )
        detached = floating_nb.nametowidget(floating_nb.tabs()[0])

        win.geometry("420x360")
        win.update_idletasks()
        floating_nb.update_idletasks()
        assert detached.winfo_width() == floating_nb.winfo_width()
        assert detached.winfo_height() == floating_nb.winfo_height()

        win.geometry("320x260")
        win.update_idletasks()
        floating_nb.update_idletasks()
        assert detached.winfo_width() == floating_nb.winfo_width()
        assert detached.winfo_height() == floating_nb.winfo_height()

        root.destroy()
