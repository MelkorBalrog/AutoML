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

"""Regression tests ensuring detached toolbars clone once and remain functional."""

from __future__ import annotations

import tkinter as tk
import pytest

from gui.utils.closable_notebook import ClosableNotebook


class TestDetachedToolbar:
    """Grouped tests verifying toolbar cloning and button events."""

    def setup_method(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        self.nb = ClosableNotebook(self.root)
        frame = tk.Frame(self.nb)
        self.nb.add(frame, text="T")
        self.toolbar = tk.Frame(frame)
        self.toolbar.pack()
        self.clicked = 0
        btn = tk.Button(self.toolbar, text="B", command=self._on_click)
        btn.bind("<Enter>", lambda _e: None)
        btn.bind("<Leave>", lambda _e: None)
        btn.pack()
        self.btn = btn

    def teardown_method(self) -> None:
        self.root.destroy()

    def _on_click(self) -> None:
        self.clicked += 1

    def _detach(self) -> tuple[ClosableNotebook, tk.Frame]:
        tab_id = self.nb.tabs()[0]
        self.nb._detach_tab(tab_id, 20, 20)
        win = self.nb._floating_windows[0]
        nb2 = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        clone_tab = nb2.tabs()[0]
        frame_clone = nb2.nametowidget(clone_tab)
        return nb2, frame_clone

    def test_single_toolbar_row_after_detach(self) -> None:
        nb2, frame_clone = self._detach()
        toolbars = [
            c
            for c in frame_clone.winfo_children()
            if isinstance(c, tk.Frame) and any(isinstance(gc, tk.Button) for gc in c.winfo_children())
        ]
        assert len(toolbars) == 1
        nb2._floating_windows[0].destroy() if getattr(nb2, "_floating_windows", []) else None

    def test_button_click_triggers_callback(self) -> None:
        _nb2, frame_clone = self._detach()
        btn_clone = next(
            c
            for c in frame_clone.winfo_children()
            if isinstance(c, tk.Frame)
        ).winfo_children()[0]
        btn_clone.invoke()
        assert self.clicked == 1
        _nb2 = None
