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

"""Regression tests for cancelling stale ``after`` callbacks on detachment."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
def test_detached_tab_cancels_widget_after(capsys):
    """Cancel callbacks referencing the top-level widget."""
    root = tk.Tk()
    root.withdraw()
    nb = ClosableNotebook(root)
    frame = tk.Frame(nb)
    btn = tk.Button(frame)
    btn.pack()
    nb.add(frame, text="Tab")
    btn.tk.call("after", "1", f"{btn} config -text hi")
    nb._detach_tab(nb.tabs()[0], 10, 10)
    root.update()
    assert "invalid command name" not in capsys.readouterr().err
    nb._floating_windows[0].destroy()
    root.destroy()


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
def test_detached_tab_cancels_child_after(capsys):
    """Cancel callbacks referencing child widgets recursively."""
    root = tk.Tk()
    root.withdraw()
    nb = ClosableNotebook(root)
    frame = tk.Frame(nb)
    inner = tk.Label(frame, text="x")
    inner.pack()
    nb.add(frame, text="Tab")
    inner.tk.call("after", "1", f"{inner} config -text hi")
    nb._detach_tab(nb.tabs()[0], 10, 10)
    root.update()
    assert "invalid command name" not in capsys.readouterr().err
    nb._floating_windows[0].destroy()
    root.destroy()
