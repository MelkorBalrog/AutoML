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

"""Canvas cloning tests ensuring widgets replicate state when detached."""

import os
import sys
import tkinter as tk
import pytest

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "gui", "utils"))
from closable_notebook import ClosableNotebook


def test_canvas_clone_retains_items() -> None:
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    nb = ClosableNotebook(root)
    canvas = tk.Canvas(nb, width=50, height=50)
    canvas.create_line(0, 0, 10, 10)
    clone, _, _ = nb._clone_widget(canvas, nb)
    assert isinstance(clone, tk.Canvas)
    assert clone.find_all(), "Cloned canvas lost its items"
    root.destroy()
