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
"""Grouped tests ensuring root-level callbacks are cancelled."""

import os
import tkinter as tk
import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestRootLevelAfterCleanup:
    """Tests for cancelling root-level ``after`` callbacks on detach."""

    def test_detach_cancels_root_level_callbacks(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        root.withdraw()
        errors: list[str] = []
        root.report_callback_exception = lambda exc, val, tb: errors.append(str(val))

        nb = ClosableNotebook(root)
        frame = tk.Frame(nb)
        nb.add(frame, text="A")
        nb.update_idletasks()

        cmd = f"{str(frame)}_animate"
        root.tk.createcommand(cmd, lambda: None)
        ident = root.tk.call("after", "1000", cmd)
        assert ident in root.tk.call("after", "info")

        nb._detach_tab(nb.tabs()[0], nb.winfo_rootx() + 50, nb.winfo_rooty() + 50)
        root.update()
        info = root.tk.call("after", "info")
        assert ident not in info
        assert not any("invalid command name" in e for e in errors)
        root.destroy()
