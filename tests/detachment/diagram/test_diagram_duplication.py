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
"""Tests ensuring detached windows contain a single canvas."""

from __future__ import annotations

import tkinter as tk
import pytest

from gui.utils.closable_notebook import ClosableNotebook


class DummyWindow(tk.Frame):
    """Stub window with a toolbox and canvas."""

    def __init__(self, master: tk.Widget):
        super().__init__(master)
        self.toolbox = tk.Frame(self, name="toolbox")
        self.toolbox.pack(side="left")
        self.canvas = tk.Canvas(self, name="diagram")
        self.canvas.pack(side="right", expand=True, fill="both")

    def _rebuild_toolboxes(self) -> None:  # pragma: no cover - simple stub
        pass

    def _activate_parent_phase(self) -> None:  # pragma: no cover - simple stub
        pass

    def _switch_toolbox(self) -> None:  # pragma: no cover - simple stub
        pass


def _detach(nb: ClosableNotebook, tab_id: str) -> DummyWindow:
    win, nb2 = nb._create_detached_window(200, 200, 0, 0)
    nb._clone_tab_contents(tab_id, nb2, "Tab", win)
    clone = nb2.nametowidget(nb2.tabs()[0])
    assert isinstance(clone, DummyWindow)
    return clone


class TestDetachedCanvasLayout:
    """Grouped tests verifying diagram duplication is avoided."""

    def test_single_canvas(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        win = DummyWindow(nb)
        nb.add(win, text="Tab")
        clone = _detach(nb, nb.tabs()[0])
        canvases = [w for w in clone.winfo_children() if isinstance(w, tk.Canvas)]
        assert canvases == [clone.canvas]
        root.destroy()

    def test_canvas_binding_invokes(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        win = DummyWindow(nb)
        nb.add(win, text="Tab")
        clone = _detach(nb, nb.tabs()[0])
        triggered: list[bool] = []
        clone.canvas.bind("<Button-1>", lambda e: triggered.append(True))
        clone.canvas.event_generate("<Button-1>")
        assert triggered == [True]
        root.destroy()
