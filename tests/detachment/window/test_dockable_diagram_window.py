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
"""Tests for the :class:`DockableDiagramWindow` utility."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.dockable_diagram_window import DockableDiagramWindow


class DummyDiagram(tk.Frame):
    """Minimal diagram stub exposing a toolbox and hooks."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.log: list[str] = []
        self.toolbox = tk.Frame(self)
        tk.Button(self.toolbox, text="B", command=lambda: self.log.append("btn")).pack()
        self.toolbox_selector = ttk.Combobox(self, values=["A", "B"])
        self.toolbox_selector.pack()

    def _rebuild_toolboxes(self) -> None:  # pragma: no cover - trivial
        self.log.append("rebuild")

    def _activate_parent_phase(self) -> None:  # pragma: no cover - trivial
        self.log.append("activate")

    def _switch_toolbox(self) -> None:  # pragma: no cover - trivial
        self.log.append("switch")


class TestDockableDiagramWindow:
    def test_dock_runs_hooks_and_hides_window(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        notebook = ClosableNotebook(root)
        notebook.pack()
        win = DockableDiagramWindow(root)
        diagram = DummyDiagram(win.content_frame)
        diagram.pack()
        win.dock(notebook, 0, "Tab")
        assert diagram.log[:3] == ["rebuild", "activate", "switch"]
        assert str(win.content_frame) in notebook.tabs()
        assert win.win.state() == "withdrawn"
        root.destroy()

    def test_float_restores_window_and_runs_hooks_again(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        notebook = ClosableNotebook(root)
        notebook.pack()
        win = DockableDiagramWindow(root)
        diagram = DummyDiagram(win.content_frame)
        diagram.pack()
        win.dock(notebook, 0, "Tab")
        count = len(diagram.log)
        win.float(10, 10, 200, 200)
        assert win.win.state() != "withdrawn"
        assert diagram.log[count:count+3] == ["rebuild", "activate", "switch"]
        root.destroy()
