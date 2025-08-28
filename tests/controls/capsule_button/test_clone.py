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

"""Regression tests for CapsuleButton cloning."""

import os
import tkinter as tk

import pytest

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))
from gui.controls.capsule_button import CapsuleButton
from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
def test_clone_preserves_text():
    root = tk.Tk()
    root.withdraw()
    btn = CapsuleButton(root, text="Hello")
    nb = ClosableNotebook(root)
    clone, _, _ = nb._clone_widget(btn, root)
    assert clone.cget("text") == "Hello"
    root.destroy()


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
def test_clone_preserves_state():
    root = tk.Tk()
    root.withdraw()
    btn = CapsuleButton(root, text="Hi", state=tk.DISABLED)
    nb = ClosableNotebook(root)
    clone, _, _ = nb._clone_widget(btn, root)
    assert clone.cget("state") == tk.DISABLED
    root.destroy()
