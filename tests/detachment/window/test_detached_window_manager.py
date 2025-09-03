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

"""Tests for the :class:`DetachedWindow` helper."""

from __future__ import annotations

import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.detached_window import DetachedWindow


class DummyDiagram(tk.Frame):
    """Diagram exposing a toolbox and selectable element."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.log: list[str] = []
        self.toolbox = tk.Frame(self, name="toolbox")
        tk.Label(self.toolbox, text="TB").pack()
        self.toolbox.pack(side="left")
        self.canvas = tk.Frame(self, name="canvas")
        self.canvas.pack(side="left")
        tk.Button(
            self.canvas, text="E", command=lambda: self.log.append("select")
        ).pack()


class TestDetachedWindowManager:
    @pytest.mark.gui
    def test_detached_window_moves_tab(self, monkeypatch: pytest.MonkeyPatch) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        frame = tk.Frame(nb)
        log: list[str] = []
        btn = tk.Button(frame, text="Go", command=lambda: log.append("clicked"))
        btn.pack()
        nb.add(frame, text="Tab")

        dw = DetachedWindow(nb, 100, 100, 0, 0)
        dw.detach_tab(nb.tabs()[0])

        assert not nb.tabs()
        assert dw.nb.tabs()
        clone = dw.nb.nametowidget(dw.nb.tabs()[0])
        clone_btn = clone.winfo_children()[0]
        clone_btn.invoke()
        assert log == ["clicked"]
        root.destroy()

    @pytest.mark.gui
    def test_detached_diagram_single_toolbox_and_selection(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        diagram = DummyDiagram(nb)
        nb.add(diagram, text="Tab")
        monkeypatch.setattr(nb, "_move_tab", lambda *a, **k: False)

        dw = DetachedWindow(nb, 100, 100, 0, 0)
        dw.detach_tab(nb.tabs()[0])

        clone = dw.nb.nametowidget(dw.nb.tabs()[0])
        toolbox_count = sum(
            1 for child in clone.winfo_children() if child.winfo_name() == "toolbox"
        )
        assert toolbox_count == 1

        canvas = clone.nametowidget("canvas")
        btn = canvas.winfo_children()[0]
        btn.invoke()
        assert diagram.log == ["select"]
        root.destroy()
