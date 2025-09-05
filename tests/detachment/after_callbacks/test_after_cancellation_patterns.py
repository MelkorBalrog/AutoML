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
"""Grouped tests for cancelling varied Tk ``after`` patterns."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from gui.utils.tk_utils import cancel_after_events


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestAfterCancellationPatterns:
    """Ensure diverse after callbacks are fully cancelled."""

    def test_widget_and_child_callbacks(self):
        root = tk.Tk(); root.withdraw()
        frame = tk.Frame(root)
        child = tk.Label(frame)
        ident_parent = frame.after(1000000, lambda: None)
        ident_child = child.after(1000000, lambda: None)
        cancel_after_events(frame)
        assert ident_parent not in frame.tk.call("after", "info", str(frame))
        assert ident_child not in child.tk.call("after", "info", str(child))
        root.destroy()

    def test_string_script_reference_removed(self):
        root = tk.Tk(); root.withdraw()
        btn = tk.Button(root)
        script = f"destroy {btn}"
        ident = root.after(1000000, script)
        cancel_after_events(btn)
        assert ident not in root.tk.call("after", "info")
        root.destroy()

    def test_custom_command_cleanup(self):
        root = tk.Tk(); root.withdraw()
        btn = tk.Button(root)
        cmd_name = f"{btn}_cmd"
        root.tk.createcommand(cmd_name, lambda: None)
        ident = root.after(1000000, cmd_name)
        cancel_after_events(btn)
        assert cmd_name not in getattr(root, "_tclCommands", {})
        assert ident not in root.tk.call("after", "info")
        root.destroy()
