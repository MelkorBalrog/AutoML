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

"""Tests for background rendering in :class:`ClosableNotebook`."""

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
def test_background_visible_without_tabs():
    root = tk.Tk()
    root.withdraw()
    nb = ClosableNotebook(root)
    root.update_idletasks()
    assert nb._bg_canvas.winfo_ismapped()

    frame = tk.Frame(nb)
    nb.add(frame, text="T1")
    root.update_idletasks()
    assert not nb._bg_canvas.winfo_ismapped()

    nb.forget(frame)
    root.update_idletasks()
    assert nb._bg_canvas.winfo_ismapped()
    root.destroy()
