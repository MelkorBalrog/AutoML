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
"""Tests for deleting numeric Tcl commands tied to widget callbacks."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook, cancel_after_events


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestNumericAfterScriptCleanup:
    """Grouped tests for numeric callback command removal."""

    def test_cancel_removes_script_command(self):
        root = tk.Tk(); root.withdraw()
        nb = ClosableNotebook(root)
        btn = tk.Button(nb, text="Go")
        nb.add(btn, text="Tab")
        cmd = f"{btn}_animate"
        root.tk.createcommand(cmd, lambda: None)
        root.tk.call("after", "1", cmd)
        cancel_after_events(btn)
        assert cmd not in getattr(root, "_tclCommands", {})
        root.destroy()
