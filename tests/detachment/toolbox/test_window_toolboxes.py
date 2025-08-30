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

"""Grouped tests ensuring detached windows retain functional toolboxes."""

from __future__ import annotations

import tkinter as tk
import pytest

from gui.utils.closable_notebook import ClosableNotebook


class DummyArchitectureWindow(tk.Frame):
    """Stub window exposing a ``toolbox`` attribute."""

    def __init__(self, master):
        super().__init__(master)
        self.toolbox = tk.Frame(self)
        self.toolbox.pack(side="left")
        self.log: list[str] = []
        tk.Button(self.toolbox, text="A", command=lambda: self.log.append("A")).pack()


class DummyStpaWindow(tk.Frame):
    """Stub window exposing a ``tools_frame`` attribute."""

    def __init__(self, master):
        super().__init__(master)
        self.tools_frame = tk.Frame(self)
        self.tools_frame.pack(side="left")
        self.log: list[str] = []
        tk.Button(self.tools_frame, text="S", command=lambda: self.log.append("S")).pack()


class DummyGsnWindow(tk.Frame):
    """Stub window with a ``toolbox`` and functional button."""

    def __init__(self, master):
        super().__init__(master)
        self.toolbox = tk.Frame(self)
        self.toolbox.pack(side="left")
        self.log: list[str] = []
        tk.Button(self.toolbox, text="G", command=lambda: self.log.append("G")).pack()


@pytest.mark.parametrize(
    "win_cls, attr",
    [
        (DummyArchitectureWindow, "toolbox"),
        (DummyStpaWindow, "tools_frame"),
        (DummyGsnWindow, "toolbox"),
    ],
)
def test_cloned_windows_pack_toolbox(win_cls, attr):
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    nb = ClosableNotebook(root)
    win = win_cls(nb)
    nb.add(win, text="Tab")
    clone, mapping, _ = nb._clone_widget(win, root)
    toolbox = getattr(clone, attr, None)
    assert isinstance(toolbox, tk.Widget)
    assert toolbox.winfo_manager() == "pack"
    btn = toolbox.winfo_children()[0]
    btn.invoke()
    assert getattr(clone, "log") == [toolbox.winfo_children()[0]["text"]]
    assert mapping[getattr(win, attr)] is toolbox
    root.destroy()
