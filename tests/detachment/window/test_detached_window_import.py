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
"""Integration tests verifying detached windows host closable notebooks."""

import os
import tkinter as tk
import pytest

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.detached_window import DetachedWindow


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestDetachedWindowImport:
    """Grouped tests for detached window imports."""

    def test_detach_tab_hosts_closable_notebook(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        root.withdraw()
        nb = ClosableNotebook(root)
        frame = tk.Frame(nb)
        nb.add(frame, text="Tab")
        dw = DetachedWindow(nb, 100, 100, 0, 0)
        dw.detach_tab(nb.tabs()[0])
        assert isinstance(dw.nb, ClosableNotebook)
        dw.win.destroy()
        root.destroy()
