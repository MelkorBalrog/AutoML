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

"""Tests for ``_remove_widget_pairs`` helper."""

import os
import tkinter as tk
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))
from gui.utils.closable_notebook import _remove_widget_pairs


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
def test_remove_widget_pairs_detaches_only_targeted_widgets():
    root = tk.Tk()
    root.withdraw()
    parent = tk.Frame(root)
    parent.pack()
    child1 = tk.Label(parent, text="A")
    child1.pack()
    child2 = tk.Label(parent, text="B")
    child2.pack()
    child3 = tk.Label(parent, text="C")
    child3.pack()

    _remove_widget_pairs(parent, [(child1, child2)])

    assert not child1.winfo_ismapped()
    assert not child2.winfo_ismapped()
    assert child3.winfo_manager() == "pack"
    assert child3 in parent.winfo_children()

    root.destroy()
