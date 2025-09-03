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

"""Regression tests for missing Tcl command entries during widget cleanup."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook, cancel_after_events


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestMissingCommandCleanup:
    """Grouped tests ensuring absent Tcl commands do not raise errors."""

    def _setup(self) -> tuple[tk.Tk, ClosableNotebook, tk.Button, str]:
        root = tk.Tk(); root.withdraw()
        nb = ClosableNotebook(root)
        btn = tk.Button(nb, text="Go")
        nb.add(btn, text="Tab")
        ident = btn.after(1, lambda: None)
        return root, nb, btn, ident

    def test_detach_missing_identifier_no_errors(self, capsys):
        root, nb, btn, ident = self._setup()
        root._tclCommands.pop(ident, None)
        nb._detach_tab(nb.tabs()[0], 10, 10)
        win = nb._floating_windows[0]
        win.destroy()
        root.update()
        err = capsys.readouterr().err
        assert "invalid command name" not in err
        assert "AttributeError" not in err
        root.destroy()

    def test_destroy_widget_missing_identifier_no_errors(self, capsys):
        root, nb, btn, ident = self._setup()
        root._tclCommands.pop(ident, None)
        btn.destroy()
        cancel_after_events(btn)
        err = capsys.readouterr().err
        assert "invalid command name" not in err
        assert "AttributeError" not in err
        root.destroy()
