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

"""Grouped tests verifying toolbar detachment resets state and actions."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


pytestmark = pytest.mark.detachment


def _detach_toolbar(
    ) -> tuple[tk.Tk, tk.Toplevel, tk.Frame, tk.Frame, ttk.Button, ttk.Button, dict[str, int]]:
    """Create a notebook with toolbar, detach it and return widgets."""

    root = tk.Tk()
    nb = ClosableNotebook(root)
    frame = tk.Frame(nb)
    nb.add(frame, text="T")
    toolbar = tk.Frame(frame)
    toolbar.pack()
    clicks: dict[str, int] = {"count": 0}

    def on_click() -> None:
        clicks["count"] += 1

    btn_click = ttk.Button(toolbar, text="Click", command=on_click)
    btn_click.pack()
    btn_hover = ttk.Button(toolbar, text="Hover")
    btn_hover.pack()
    btn_hover.state(["active"])
    nb.update_idletasks()
    tab_id = nb.tabs()[0]
    nb._detach_tab(tab_id, 50, 50)
    win = nb._floating_windows[0]
    nb2 = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
    clone_frame = nb2.nametowidget(nb2.tabs()[0])
    clone_toolbar = next(
        c for c in clone_frame.winfo_children() if isinstance(c, tk.Frame)
    )
    clone_click = clone_toolbar.winfo_children()[0]
    clone_hover = clone_toolbar.winfo_children()[1]
    return root, win, toolbar, clone_toolbar, clone_click, clone_hover, clicks


class TestToolbarDetachment:
    """Grouped cases covering toolbar duplicates, hover state and callbacks."""

    def test_duplicate_buttons_removed(self) -> None:
        try:
            root, win, orig_toolbar, clone_toolbar, _click, _hover, _clicks = _detach_toolbar()
        except tk.TclError:
            pytest.skip("Tk not available")
        assert len(clone_toolbar.winfo_children()) == len(orig_toolbar.winfo_children())
        win.destroy()
        root.destroy()

    def test_hover_state_resets_on_detach(self) -> None:
        try:
            root, win, _orig_toolbar, _clone_toolbar, _click, clone_hover, _clicks = _detach_toolbar()
        except tk.TclError:
            pytest.skip("Tk not available")
        assert clone_hover.instate(["!active"])
        win.destroy()
        root.destroy()

    def test_click_callback_survives_detach(self) -> None:
        try:
            root, win, _orig_toolbar, _clone_toolbar, clone_click, _hover, clicks = _detach_toolbar()
        except tk.TclError:
            pytest.skip("Tk not available")
        clone_click.invoke()
        assert clicks["count"] == 1
        win.destroy()
        root.destroy()
