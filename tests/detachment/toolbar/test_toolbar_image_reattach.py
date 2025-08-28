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

"""Regression tests ensuring toolbar images survive detach/reattach."""

from __future__ import annotations

import tkinter as tk
import pytest

from gui.utils.closable_notebook import ClosableNotebook


class TestToolbarImageReattach:
    """Grouped tests verifying toolbar button images stay intact."""

    def setup_method(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        self.nb = ClosableNotebook(self.root)
        frame = tk.Frame(self.nb)
        self.nb.add(frame, text="T")
        self.img = tk.PhotoImage(width=16, height=16)
        self.btn = tk.Button(frame, image=self.img, compound="left")
        self.btn.image = self.img
        self.btn.pack()
        self.orig_name = self.btn.cget("image")
        self.orig_size = (self.img.width(), self.img.height())

    def teardown_method(self) -> None:
        self.root.destroy()

    def test_detach_and_reattach_keeps_image_size(self) -> None:
        tab_id = self.nb.tabs()[0]
        self.nb._detach_tab(tab_id, 50, 50)
        win = self.nb._floating_windows[0]
        nb2 = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        clone_tab = nb2.tabs()[0]
        frame_clone = nb2.nametowidget(clone_tab)
        btn_clone = next(c for c in frame_clone.winfo_children() if isinstance(c, tk.Button))
        assert " " not in btn_clone.cget("image")
        nb2._move_tab(clone_tab, self.nb)
        new_name = btn_clone.cget("image")
        assert new_name != self.orig_name
        assert (btn_clone.image.width(), btn_clone.image.height()) == self.orig_size
        win.destroy()
