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

"""Regression tests for after-callback cleanup when closing tabs."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestTabCloseAfterCallbacks:
    """Grouped tests covering tab closure and detachment cleanup."""

    class AnimatedButton(tk.Button):
        def __init__(self, master: tk.Widget) -> None:
            super().__init__(master, text="Go")
            # Schedule using the root so the identifier is not bound to the widget
            self._pulse_animate = self._root().tk.call("after", "1", f"{self} config -text hi")

    def _detach(self, nb: ClosableNotebook, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(nb, "_move_tab", lambda tab_id, target: False)

        class Event:
            ...

        press = Event()
        press.x = 5
        press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

    def test_close_tab_no_invalid_command_name(self, capsys):
        root = tk.Tk(); root.withdraw()
        nb = ClosableNotebook(root)
        btn = self.AnimatedButton(nb)
        nb.add(btn, text="Tab")
        nb._cancel_after_events(btn)
        btn.destroy()
        root.update()
        assert "invalid command name" not in capsys.readouterr().err
        root.destroy()

    def test_detach_tab_no_invalid_command_name(self, monkeypatch, capsys):
        root = tk.Tk(); root.withdraw()
        nb = ClosableNotebook(root)
        btn = self.AnimatedButton(nb)
        nb.add(btn, text="Tab")
        nb.update_idletasks()
        self._detach(nb, monkeypatch)
        win = nb._floating_windows[0]
        win.destroy()
        root.update()
        assert "invalid command name" not in capsys.readouterr().err
        root.destroy()
