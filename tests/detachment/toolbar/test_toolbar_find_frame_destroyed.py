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

"""Tests for toolbar frame detection with destroyed widgets."""

from __future__ import annotations

import tkinter as tk
import pytest

from gui.utils.closable_notebook import ClosableNotebook


class TestToolbarFrameDetection:
    """Grouped tests verifying toolbar frame lookup robustness."""

    def test_handles_destroyed_widget(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        frame = tk.Frame(nb)
        nb.add(frame, text="T")
        btn = tk.Button(frame, text="B")
        btn.pack()
        frame.destroy()
        assert nb._find_toolbar_frame(frame) is None
        root.destroy()
