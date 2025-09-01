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

"""Regression tests for after-callback cleanup on window detachment/closure."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook, cancel_after_events


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestAfterCallbackErrors:
    """Grouped tests ensuring no errors from cancelled ``after`` callbacks."""

    def _setup(self) -> tuple[tk.Tk, ClosableNotebook, tk.Button]:
        root = tk.Tk(); root.withdraw()
        nb = ClosableNotebook(root)
        btn = tk.Button(nb, text="Go")
        nb.add(btn, text="Tab")
        btn.tk.call("after", "1", f"{btn} config -text hi")
        return root, nb, btn

    def test_detach_window_no_errors(self, capsys):
        root, nb, _btn = self._setup()
        nb._detach_tab(nb.tabs()[0], 10, 10)
        win = nb._floating_windows[0]
        win.destroy()
        root.update()
        err = capsys.readouterr().err
        assert "invalid command name" not in err
        assert "AttributeError" not in err
        root.destroy()

    def test_destroyed_root_no_attribute_error(self, capsys):
        root, nb, btn = self._setup()
        nb._detach_tab(nb.tabs()[0], 10, 10)
        root.destroy()
        cancel_after_events(btn)
        err = capsys.readouterr().err
        assert "invalid command name" not in err
        assert "AttributeError" not in err

