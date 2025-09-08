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

"""Ensure ``reparent_widget`` falls back when ``SetParent`` fails."""

from __future__ import annotations

import ctypes
import tkinter as tk

import pytest

from gui.utils import tk_utils


@pytest.mark.detachment
@pytest.mark.reparenting
class TestReparentFallback:
    def test_windows_setparent_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        parent = tk.Frame(root)
        parent.pack()
        child = tk.Frame(root)
        child.pack()

        monkeypatch.setattr(tk_utils.sys, "platform", "win32")

        class DummyUser32:
            @staticmethod
            def SetParent(_wid: int, _pid: int) -> int:
                return 0

        monkeypatch.setattr(ctypes, "windll", type("W", (), {"user32": DummyUser32()})())

        tk_utils.reparent_widget(child, parent)
        assert child.master is parent
        root.destroy()
