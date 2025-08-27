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

"""Tests for releasing dragged tabs over empty screen space."""

from __future__ import annotations

import tkinter as tk
import pytest
from gui.utils.closable_notebook import ClosableNotebook


class TestDragReleaseOverVoid:
    def test_creates_floating_window(self) -> None:
        """Dragging a tab to empty space should create a new window."""
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        root.report_callback_exception = lambda exc, val, tb: (_ for _ in ()).throw(val)

        nb = ClosableNotebook(root)
        frame = tk.Frame(nb)
        nb.add(frame, text="Tab1")
        nb.update_idletasks()

        class Event: ...

        press = Event()
        press.x = 5
        press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True

        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        assert nb._floating_windows, "Expected floating window after detachment"
        root.destroy()
