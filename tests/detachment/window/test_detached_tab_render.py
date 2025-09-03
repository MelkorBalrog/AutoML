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
"""Regression tests ensuring detached tabs render regardless of layouts mapping."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.detached_window import DetachedWindow


class TestDetachedTabRender:
    """Grouped tests verifying detached tab rendering."""

    @pytest.mark.parametrize("use_layouts", [False, True])
    def test_tab_renders_with_or_without_layouts(self, use_layouts: bool) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        frame = ttk.Frame(nb)
        ttk.Label(frame, text="Hello").pack()
        nb.add(frame, text="Tab")
        dw = DetachedWindow(root, width=100, height=100, x=0, y=0)
        mapping: dict[tk.Widget, tk.Widget] = {}
        kwargs = {"layouts": {}} if use_layouts else {}
        clone, mapping, _layouts = nb._clone_widget(frame, dw.nb, mapping, **kwargs)
        dw.add(clone, "Tab")
        root.update_idletasks()
        lbl = clone.winfo_children()[0]
        assert lbl.winfo_manager()  # label should be managed (rendered)
        root.destroy()
