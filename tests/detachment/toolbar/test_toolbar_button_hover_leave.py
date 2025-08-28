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
"""Regression tests for hover and click behaviour on detached toolbar buttons."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


class TestDetachedToolbarHoverAndClick:
    """Grouped tests verifying hover reset and callback invocation."""

    def setup_method(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        self.nb = ClosableNotebook(self.root)
        frame = tk.Frame(self.nb)
        self.nb.add(frame, text="T")
        toolbar = tk.Frame(frame)
        toolbar.pack()
        self.clicked = {"count": 0}

        def on_click() -> None:
            self.clicked["count"] += 1

        btn = ttk.Button(toolbar, text="B", command=on_click)
        btn.bind("<Enter>", lambda _e: btn.state(["active"]))
        btn.bind("<Leave>", lambda _e: btn.state(["!active"]))
        btn.pack()
        tab_id = self.nb.tabs()[0]
        self.nb._detach_tab(tab_id, 50, 50)
        win = self.nb._floating_windows[0]
        nb2 = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        clone_frame = nb2.nametowidget(nb2.tabs()[0])
        self.clone_btn = next(
            c for c in clone_frame.winfo_children() if isinstance(c, ttk.Button)
        )
        self.win = win

    def teardown_method(self) -> None:
        if getattr(self, "win", None) and self.win.winfo_exists():
            self.win.destroy()
        self.root.destroy()

    def test_hover_state_resets_on_leave(self) -> None:
        self.clone_btn.event_generate("<Enter>")
        assert self.clone_btn.instate(["active"])
        self.clone_btn.event_generate("<Leave>")
        assert self.clone_btn.instate(["!active"])

    def test_click_invokes_callback(self) -> None:
        self.clone_btn.invoke()
        assert self.clicked["count"] == 1
