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

"""Regression tests for destroying windows with pending animation callbacks."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestDestroyWithAnimation:
    """Grouped tests for detaching tabs then destroying their windows."""

    class Animated(tk.Button):
        def __init__(self, master: tk.Widget) -> None:
            super().__init__(master, text="Go")
            self._spin_after = self.after(1, self._spin)

        def _spin(self) -> None:
            self._spin_after = self.after(1, self._spin)

    def test_no_errors_on_destroy(self, capsys):
        root = tk.Tk(); root.withdraw()
        errors: list[Exception] = []
        root.report_callback_exception = lambda exc, val, tb: errors.append(val)
        nb = ClosableNotebook(root)
        btn = self.Animated(nb)
        nb.add(btn, text="Tab")
        nb.update_idletasks()
        nb._detach_tab(nb.tabs()[0], 10, 10)
        nb._floating_windows[0].destroy()
        root.destroy()
        assert "invalid command name" not in capsys.readouterr().err
        assert not any(isinstance(e, AttributeError) for e in errors)
