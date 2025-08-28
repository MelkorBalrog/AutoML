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

"""Tests for target notebook lookup when widgets vanish mid-drag."""

from __future__ import annotations

import tkinter as tk
import pytest

from gui.utils.closable_notebook import ClosableNotebook


class TestTargetNotebookDestroyedWidget:
    """Group target lookup tests when widgets are destroyed."""

    def test_release_over_destroyed_widget_keyerror(self) -> None:
        """Simulate KeyError from ``winfo_containing`` during release."""
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        frame = tk.Frame(nb)
        nb.add(frame, text="Tab1")
        nb.update_idletasks()

        class Event: ...

        press = Event()
        press.x = press.y = 0
        nb._on_tab_press(press)
        nb._dragging = True

        def explode(_x: int, _y: int) -> tk.Widget:  # type: ignore[override]
            raise KeyError("widget destroyed")

        nb.winfo_containing = explode  # type: ignore[assignment]

        release = Event()
        release.x_root = release.y_root = 0
        nb._on_tab_release(release)

        assert nb._floating_windows
        root.destroy()
