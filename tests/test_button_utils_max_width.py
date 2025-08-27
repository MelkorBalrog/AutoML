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

"""Tests for toolbox button width utilities."""

import os
import tkinter as tk
from tkinter import ttk

import pytest

from gui.controls.button_utils import max_button_reqwidth


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
def test_max_button_reqwidth_ignores_destroyed_widgets():
    root = tk.Tk()
    root.withdraw()
    frame = ttk.Frame(root)
    frame.pack()
    btn = ttk.Button(frame, text="Sample")
    btn.pack()
    root.update_idletasks()

    # Ensure width measured while button exists
    assert max_button_reqwidth(frame) == btn.winfo_reqwidth()

    # Destroy button and ensure function handles it gracefully
    btn.destroy()
    root.update_idletasks()
    assert max_button_reqwidth(frame) == 0
    root.destroy()
