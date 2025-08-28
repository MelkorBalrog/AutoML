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
"""Grouped tests verifying after-event cleanup during detachment."""

import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import cancel_after_events


class TestAfterCleanup:
    """Ensure scheduled callbacks are cancelled before destruction."""

    def test_cancelled_child_events_do_not_raise(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        lbl = ttk.Label(root)
        lbl.pack()
        lbl.after(1, lambda: None)
        cancel_after_events(root)
        root.destroy()

    def test_cancelled_root_events_do_not_raise(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        root._after = root.after(1, lambda: None)
        cancel_after_events(root)
        root.destroy()
