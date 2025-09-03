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
"""Grouped tests covering detachment clone fallback."""

import os
import tkinter as tk
import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestCloneTabFallback:
    """Ensure detachment clones widgets when moving fails."""

    def test_detach_uses_clone_when_move_fails(self, monkeypatch):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        root.withdraw()

        nb = ClosableNotebook(root)
        frame = tk.Frame(nb)
        nb.add(frame, text="A")
        nb.update_idletasks()

        def forced_fail(self, tab_id, target):
            return False

        monkeypatch.setattr(ClosableNotebook, "_move_tab", forced_fail)

        nb._detach_tab(nb.tabs()[0], nb.winfo_rootx() + 40, nb.winfo_rooty() + 40)
        assert nb._floating_windows
        win = nb._floating_windows[-1]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        assert len(new_nb.tabs()) == 1
        root.destroy()
