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

"""Tests for drag finalization when widgets are destroyed mid-operation."""

from __future__ import annotations

import tkinter as tk
import pytest
from gui.utils.closable_notebook import ClosableNotebook


class TestFinalizeDragDestroyedWidget:
    def test_finalize_drag_ignores_destroyed_widget(self) -> None:
        """_finalize_drag should not raise if the tab widget was destroyed."""
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        root.report_callback_exception = lambda exc, val, tb: (_ for _ in ()).throw(val)

        nb = ClosableNotebook(root)
        frame = tk.Frame(nb)
        nb.add(frame, text="Tab1")
        nb.update_idletasks()

        nb._dragging = True
        class Event: ...
        event = Event()
        event.x = event.y = 0
        event.x_root = event.y_root = 0

        frame.destroy()

        nb._finalize_drag(0, event)
        root.destroy()
