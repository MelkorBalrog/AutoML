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

"""Regression tests for standard Button hover state after detachment."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestDetachedButtonHover:
    """Grouped tests verifying Button hover behaviour in detached tabs."""

    def _setup(self) -> tuple[tk.Tk, ClosableNotebook, tk.Button]:
        root = tk.Tk()
        root.withdraw()
        root.report_callback_exception = lambda exc, val, tb: (_ for _ in ()).throw(val)
        nb = ClosableNotebook(root)
        btn = tk.Button(nb, text="Hover")
        nb.add(btn, text="Tab")
        nb._detach_tab(nb.tabs()[0], 10, 10)
        nb.update_idletasks()
        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        clone_btn = next(w for w in new_nb.winfo_children() if isinstance(w, tk.Button))
        return root, nb, clone_btn

    def test_enter_sets_active(self) -> None:
        root, nb, btn = self._setup()
        btn.event_generate("<Enter>")
        root.update()
        assert btn["state"] == "active"
        nb._floating_windows[0].destroy()
        root.destroy()

    def test_leave_restores_normal(self) -> None:
        root, nb, btn = self._setup()
        btn.event_generate("<Enter>")
        btn.event_generate("<Leave>")
        root.update()
        assert btn["state"] == "normal"
        nb._floating_windows[0].destroy()
        root.destroy()
