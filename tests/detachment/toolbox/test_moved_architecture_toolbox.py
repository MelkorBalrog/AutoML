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
"""Grouped tests for moved architecture windows retaining toolboxes."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import pytest

from gui.utils.closable_notebook import ClosableNotebook


class ArchitectureDiagram(ttk.Frame):
    """Minimal architecture diagram exposing a toolbox."""

    def __init__(self, master: tk.Widget):
        super().__init__(master)
        self.rebuilt = False
        self.switched = False
        self.activated = False
        self.clicked = False
        self.toolbox = ttk.Frame(self)
        self.toolbox.pack(side="left")
        self.tools_frame = ttk.Frame(self.toolbox)
        self.tools_frame.pack(side="left")
        self.button = ttk.Button(self.tools_frame, text="Tool", command=self._on_click)
        self.button.pack()

    def _on_click(self) -> None:  # pragma: no cover - simple flag setter
        self.clicked = True

    def _rebuild_toolboxes(self) -> None:  # pragma: no cover - simple flag setter
        self.rebuilt = True

    def _activate_parent_phase(self) -> None:  # pragma: no cover - simple flag setter
        self.activated = True

    def _switch_toolbox(self) -> None:  # pragma: no cover - simple flag setter
        self.switched = True


class TestMovedArchitectureToolbox:
    """Grouped tests verifying moved tabs keep functional toolboxes."""

    def test_toolbox_packed_after_move(self, monkeypatch):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        diagram = ArchitectureDiagram(nb)
        nb.add(diagram, text="A")
        nb.update_idletasks()

        orig_move = ClosableNotebook._move_tab

        def forced_move(self, tab_id, target):
            orig_move(self, tab_id, target)
            return True

        monkeypatch.setattr(ClosableNotebook, "_move_tab", forced_move)

        class Event:  # pragma: no cover - simple namespace
            pass

        press = Event()
        press.x = 5
        press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        moved = new_nb.nametowidget(new_nb.tabs()[0])
        assert moved.rebuilt is True
        assert moved.switched is True
        assert moved.activated is True
        assert moved.tools_frame.winfo_manager() == "pack"
        x = moved.button.winfo_rootx() + 1
        y = moved.button.winfo_rooty() + 1
        assert win.winfo_containing(x, y) == moved.button
        moved.button.invoke()
        assert moved.clicked is True
        root.destroy()
