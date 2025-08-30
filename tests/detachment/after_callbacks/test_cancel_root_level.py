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
"""Regression tests for cancelling root-level after callbacks."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import cancel_after_events


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestCancelRootLevel:
    """Grouped tests ensuring root-level callbacks are cancelled."""

    def test_detach_and_close_no_invalid_command(self, capsys):
        root = tk.Tk(); root.withdraw()
        top = tk.Toplevel(root)
        btn = tk.Button(top, text="Go")
        btn.pack()
        # Schedule root-level callback referencing the button without saving the ID
        root.tk.call("after", "1", f"{str(btn)} configure -text Foo")
        cancel_after_events(top)
        top.destroy()
        root.update()
        assert "invalid command name" not in capsys.readouterr().err
        root.destroy()
