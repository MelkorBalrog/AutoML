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

"""Integration tests for toolbar button commands in detached tabs."""

from __future__ import annotations

import tkinter as tk
import pytest

from gui.utils.closable_notebook import ClosableNotebook


class _CommandFrame(tk.Frame):
    def __init__(self, master: tk.Misc, flag: dict[str, bool]) -> None:
        super().__init__(master)
        self.flag = flag

    def flip(self) -> None:
        self.flag["flipped"] = True


class TestToolbarButtonCommand:
    """Grouped tests verifying button commands survive detachment."""

    def setup_method(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        self.nb = ClosableNotebook(self.root)
        self.flag: dict[str, bool] = {"flipped": False}
        frame = _CommandFrame(self.nb, self.flag)
        self.nb.add(frame, text="T")
        btn = tk.Button(frame, text="F", command=frame.flip)
        btn.pack()

    def teardown_method(self) -> None:
        self.root.destroy()

    def test_detached_button_invokes_container_method(self) -> None:
        tab_id = self.nb.tabs()[0]
        self.nb._detach_tab(tab_id, 50, 50)
        win = self.nb._floating_windows[0]
        nb2 = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        clone_tab = nb2.tabs()[0]
        frame_clone = nb2.nametowidget(clone_tab)
        btn_clone = next(c for c in frame_clone.winfo_children() if isinstance(c, tk.Button))
        cmd = btn_clone.cget("command")
        assert getattr(cmd, "__self__", None) is frame_clone
        btn_clone.invoke()
        assert self.flag["flipped"] is True
        win.destroy()

