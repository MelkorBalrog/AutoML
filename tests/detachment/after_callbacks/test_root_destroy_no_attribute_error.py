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

"""Ensure destroying the root after detaching leaves no AttributeError."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestRootDestroyCleanup:
    """Grouped tests verifying root destruction remains error-free."""

    class AnimatedButton(tk.Button):
        def __init__(self, master: tk.Widget) -> None:
            super().__init__(master, text="Go")
            self._pulse_after = self.after(1, self._pulse)

        def _pulse(self) -> None:
            self._pulse_after = self.after(1, self._pulse)

    def test_root_destroy_no_attribute_error(self, monkeypatch):
        root = tk.Tk(); root.withdraw()
        errors: list[Exception] = []
        root.report_callback_exception = lambda exc, val, tb: errors.append(val)
        nb = ClosableNotebook(root)
        btn = self.AnimatedButton(nb)
        nb.add(btn, text="Tab")
        nb.update_idletasks()
        monkeypatch.setattr(nb, "_move_tab", lambda tab_id, target: False)

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        win = nb._floating_windows[0]
        win.destroy()
        root.update()
        root.destroy()
        assert not any(isinstance(e, AttributeError) for e in errors)
