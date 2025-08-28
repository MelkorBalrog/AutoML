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

"""Regression tests for toolbox visibility and selector state after detachment."""

import os
import sys
import tkinter as tk
from tkinter import ttk
import pytest

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "gui", "utils"))
from closable_notebook import ClosableNotebook


class DummyDiagram(ttk.Frame):
    """Minimal diagram with toolbox and select button."""

    def __init__(self, master: tk.Widget):
        super().__init__(master)
        self.rebuilt = False
        self.activated = False
        self.switched = False
        self.current_tool = "Select"
        self.toolbox_canvas = tk.Canvas(self, width=40, height=40)
        self.toolbox_canvas.pack()
        self.toolbox = ttk.Frame(self.toolbox_canvas)
        self.toolbox_canvas.create_window(0, 0, window=self.toolbox, anchor="nw")
        self.selector = ttk.Button(self.toolbox, text="Select", command=self._on_click)
        self.selector.pack()
        self.clicks = 0

    def _on_click(self) -> None:
        self.clicks += 1

    def _rebuild_toolboxes(self) -> None:
        self.rebuilt = True

    def _activate_parent_phase(self) -> None:
        self.activated = True

    def _switch_toolbox(self) -> None:
        self.switched = True


def _detach_diagram() -> tuple[tk.Misc, tk.Toplevel, DummyDiagram]:
    """Create a diagram, detach it and return the root, window and clone."""

    root = tk.Tk()
    nb = ClosableNotebook(root)
    diagram = DummyDiagram(nb)
    nb.add(diagram, text="D")
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


class TestGovernanceToolboxDetachment:
    """Grouped tests for detached toolbox behaviour."""

    def test_toolbox_and_selector_visible(self) -> None:
        try:
            root, win, clone = _detach_diagram()
        except tk.TclError:
            pytest.skip("Tk not available")
        assert clone.rebuilt is True
        assert clone.activated is True
        assert clone.switched is True
        assert clone.toolbox.winfo_manager() == "pack"
        assert clone.toolbox.pack_info().get("side") == "left"
        x = clone.selector.winfo_rootx() + 1
        y = clone.selector.winfo_rooty() + 1
        assert win.winfo_containing(x, y) == clone.selector
        clone.selector.invoke()
        assert clone.clicks == 1
        root.destroy()

    def test_select_tool_remains_active(self) -> None:
        try:
            root, _win, clone = _detach_diagram()
        except tk.TclError:
            pytest.skip("Tk not available")
        assert clone.current_tool == "Select"
        root.destroy()
