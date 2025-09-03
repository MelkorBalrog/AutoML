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
"""Grouped tests verifying detached window creation fallbacks."""

import os
import tkinter as tk
import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestDetachedWindowCreation:
    """Grouped tests for detached window creation APIs."""

    def test_create_detached_window_returns_notebook(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        root.withdraw()
        nb = ClosableNotebook(root)
        win, nb2 = nb._create_detached_window(100, 100, 0, 0)
        assert isinstance(nb2, ClosableNotebook)
        win.destroy()
        root.destroy()

    def test_create_floating_window_without_detached_method(self, monkeypatch):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        root.withdraw()
        nb = ClosableNotebook(root)
        monkeypatch.delattr(ClosableNotebook, "_create_detached_window", raising=False)
        win, nb2 = nb._create_floating_window(100, 100, 0, 0)
        assert isinstance(nb2, ClosableNotebook)
        win.destroy()
        root.destroy()
