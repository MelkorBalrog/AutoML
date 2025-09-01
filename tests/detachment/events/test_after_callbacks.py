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

"""Regression tests for ``after`` callback cleanup on detachment."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
def test_detach_tab_leaves_no_after_callbacks(tk_root, capsys):
    """Detaching a tab cancels callbacks referencing the original widget."""
    nb = ClosableNotebook(tk_root)
    frame = tk.Frame(nb)
    btn = tk.Button(frame)
    btn.pack()
    nb.add(frame, text="Tab")
    btn.tk.call("after", "1", f"{btn} config -text hi")
    nb._detach_tab(nb.tabs()[0], 10, 10)
    tk_root.update()
    err = capsys.readouterr().err
    assert "TclError" not in err and "invalid command name" not in err
    tcl_name = str(btn)
    ids = tk_root.tk.call("after", "info")
    if isinstance(ids, str):
        ids = [ids]
    assert not any(
        tcl_name in tk_root.tk.call("after", "info", i) or tcl_name in str(i)
        for i in ids
    )
    nb.close_all_floating()


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
def test_close_detached_tab_cancels_after_callbacks(tk_root, capsys):
    """Destroying a detached window leaves no pending callbacks."""
    nb = ClosableNotebook(tk_root)
    frame = tk.Frame(nb)
    lbl = tk.Label(frame, text="x")
    lbl.pack()
    nb.add(frame, text="Tab")
    lbl.tk.call("after", "1", f"{lbl} config -text hi")
    nb._detach_tab(nb.tabs()[0], 10, 10)
    tk_root.update()
    win = nb._floating_windows[0]
    win.destroy()
    tk_root.update()
    err = capsys.readouterr().err
    assert "TclError" not in err and "invalid command name" not in err
    tcl_name = str(lbl)
    ids = tk_root.tk.call("after", "info")
    if isinstance(ids, str):
        ids = [ids]
    assert not any(
        tcl_name in tk_root.tk.call("after", "info", i) or tcl_name in str(i)
        for i in ids
    )
