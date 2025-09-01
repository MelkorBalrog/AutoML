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

"""Regression tests for Treeview hover highlight after tab detachment."""

import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))
from gui.controls.button_utils import enable_listbox_hover_highlight
from gui.utils.closable_notebook import ClosableNotebook


class TestTreeviewHoverDetached:
    """Grouped tests for Treeview hover in detached tabs."""

    @pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
    def test_hover_no_exception(self) -> None:
        """Moving over a detached Treeview should not raise errors."""

        root = tk.Tk()
        root.withdraw()
        enable_listbox_hover_highlight(root)
        nb = ClosableNotebook(root)
        frame = ttk.Frame(nb)
        tree = ttk.Treeview(frame, columns=("c",), show="headings")
        tree.insert("", "end", iid="0", values=("a",))
        tree.pack()
        nb.add(frame, text="Tab")
        nb.pack()
        root.update()

        nb._detach_tab(nb.tabs()[0], 10, 10)
        win = nb._floating_windows[0]

        x, y, _, _ = tree.bbox("0")
        tree.event_generate("<Motion>", x=x + 1, y=y + 1)
        win.update()

        assert tree.tag_has("hover", "0")

        win.destroy()
        root.destroy()

