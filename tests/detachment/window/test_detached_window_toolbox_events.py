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
        win = DetachedWindow(root, 200, 200, 10, 10)
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
        win = DetachedWindow(root, 200, 200, 10, 10)
        win.add(diagram, "Tab")
        count = diagram.log.count("switch")
        diagram.toolbox_selector.event_generate("<<ComboboxSelected>>")
        assert diagram.log.count("switch") == count + 1
        root.destroy()
