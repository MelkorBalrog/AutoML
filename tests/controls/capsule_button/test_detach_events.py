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

"""Event handling tests for :class:`CapsuleButton` after detachment."""

import pathlib
import sys
import tkinter as tk

import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

from gui.controls.capsule_button import CapsuleButton


class TestCapsuleButtonDetachedEvents:
    """Grouped tests exercising events on a destroyed button."""

    def _create_button(self) -> tuple[tk.Tk, CapsuleButton]:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        btn = CapsuleButton(root, text="Demo")
        btn.pack()
        root.update_idletasks()
        return root, btn

    def test_hover_after_detach(self) -> None:
        root, btn = self._create_button()
        btn.destroy()
        event = tk.Event()  # type: ignore[call-arg]
        btn._on_enter(event)
        root.destroy()

    def test_motion_after_detach(self) -> None:
        root, btn = self._create_button()
        btn.destroy()
        event = tk.Event()  # type: ignore[call-arg]
        event.x = 0
        event.y = 0
        btn._on_motion(event)
        root.destroy()

    def test_leave_after_detach(self) -> None:
        root, btn = self._create_button()
        btn.destroy()
        event = tk.Event()  # type: ignore[call-arg]
        btn._on_leave(event)
        root.destroy()
