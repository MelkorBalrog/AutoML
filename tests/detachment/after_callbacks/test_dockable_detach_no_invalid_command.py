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

"""Ensure dockable diagram detachment cancels ``after`` callbacks."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.dockable_diagram_window import DockableDiagramWindow


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestDockableDetachAfterCallbacks:
    """Grouped tests for dockable detachment after callbacks."""

    def test_detach_cancels_callbacks(self, capsys: pytest.CaptureFixture[str]) -> None:
        root = tk.Tk(); root.withdraw()
        nb = ClosableNotebook(root)
        frame = tk.Frame(nb)
        dock = DockableDiagramWindow(frame)
        frame._dock_window = dock
        nb.add(frame, text="Tab")
        frame._pulse_after = frame.after(1, lambda: None)
        nb._detach_tab(str(frame), 100, 100)
        root.update()
        assert "invalid command name" not in capsys.readouterr().err
        if nb._floating_windows:
            nb._floating_windows[0].destroy()
        root.destroy()
