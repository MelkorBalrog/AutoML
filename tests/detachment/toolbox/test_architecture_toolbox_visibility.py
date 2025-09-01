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

"""Grouped tests verifying detached architecture windows retain toolboxes."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import pytest

from gui.utils.closable_notebook import ClosableNotebook


class ArchitectureDiagram(ttk.Frame):
    """Minimal architecture diagram exposing a ``tools_frame``."""

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

    def _on_click(self) -> None:
        self.clicked = True

    def _rebuild_toolboxes(self) -> None:
        self.rebuilt = True

    def _activate_parent_phase(self) -> None:
        self.activated = True

    def _switch_toolbox(self) -> None:
        self.switched = True


def _detach_architecture_diagram() -> tuple[tk.Misc, tk.Toplevel, ArchitectureDiagram]:
    """Create an architecture diagram, detach it and return root, window and clone."""

    root = tk.Tk()
    nb = ClosableNotebook(root)
    diagram = ArchitectureDiagram(nb)
    nb.add(diagram, text="A")
    nb.update_idletasks()

    class Event:
        ...

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
    clone = new_nb.nametowidget(new_nb.tabs()[0])
    return root, win, clone


class TestArchitectureToolboxVisibility:
    """Grouped tests for detached architecture toolbox behaviour."""

    def test_toolbox_packed(self) -> None:
        try:
            root, _win, clone = _detach_architecture_diagram()
        except tk.TclError:
            pytest.skip("Tk not available")
        assert clone.rebuilt is True
        assert clone.switched is True
        assert clone.activated is True
        assert clone.tools_frame.winfo_manager() == "pack"
        root.destroy()

    def test_toolbox_button_responsive(self) -> None:
        try:
            root, win, clone = _detach_architecture_diagram()
        except tk.TclError:
            pytest.skip("Tk not available")
        x = clone.button.winfo_rootx() + 1
        y = clone.button.winfo_rooty() + 1
        assert win.winfo_containing(x, y) == clone.button
        clone.button.invoke()
        assert clone.clicked is True
        root.destroy()
