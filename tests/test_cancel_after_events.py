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

"""Tests for cancelling lingering Tk ``after`` callbacks."""

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
def test_cancel_after_events_cancels_animate(monkeypatch):
    root = tk.Tk()
    root.withdraw()
    btn = tk.Button(root)
    # Schedule a bogus Tcl command ending with ``_animate`` to mirror real-world animations
    ident = btn.tk.call("after", "1000000", "12345_animate")
    nb = ClosableNotebook(root)
    nb._cancel_after_events(btn)
    assert ident not in btn.tk.call("after", "info")
    root.destroy()
