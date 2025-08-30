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

"""Event binding command rewrite tests for detached widgets."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
def test_hover_command_targets_clone(tk_root):
    """Detaching rewrites bound hover commands to operate on the clone."""
    nb = ClosableNotebook(tk_root)
    frame = tk.Frame(nb)
    btn = tk.Button(frame, text="x")
    btn.bind("<Enter>", f"{btn} config -text hover")
    btn.pack()
    nb.add(frame, text="Tab")
    nb._detach_tab(nb.tabs()[0], 10, 10)
    tk_root.update()
    win = nb._floating_windows[0]
    clone = win.winfo_children()[0].winfo_children()[0]
    clone.event_generate("<Enter>")
    assert clone.cget("text") == "hover"
    nb.close_all_floating()


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
def test_click_command_targets_clone(tk_root):
    """Detaching rewrites click bindings to operate on the clone."""
    nb = ClosableNotebook(tk_root)
    frame = tk.Frame(nb)
    btn = tk.Button(frame, text="x")
    btn.bind("<Button-1>", f"{btn} config -text clicked")
    btn.pack()
    nb.add(frame, text="Tab")
    nb._detach_tab(nb.tabs()[0], 10, 10)
    tk_root.update()
    win = nb._floating_windows[0]
    clone = win.winfo_children()[0].winfo_children()[0]
    clone.event_generate("<Button-1>")
    assert clone.cget("text") == "clicked"
    nb.close_all_floating()
