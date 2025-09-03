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

import tkinter as tk
import pytest

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.detached_window import DetachedWindow


@pytest.mark.gui
def test_detached_window_moves_tab(monkeypatch):
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
