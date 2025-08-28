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

"""Regression tests for CapsuleButton ``_animate`` callbacks."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from gui.controls.capsule_button import CapsuleButton
from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestCapsuleButtonAnimateCleanup:
    """Grouped tests for ``_animate`` callback cancellation."""

    class AnimatedButton(CapsuleButton):
        def __init__(self, master: tk.Widget) -> None:
            super().__init__(master, text="Go")
            self._animate_id = self.after(1, self._animate)

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

    def test_detach_clears_animate(self, monkeypatch):
        root = tk.Tk(); root.withdraw()
        nb = ClosableNotebook(root)
        btn = self.AnimatedButton(nb)
        nb.add(btn, text="Tab")
        nb.update_idletasks()
        self._detach(nb, monkeypatch)
        root.update()
        assert "_animate" not in str(root.tk.call("after", "info"))
        win = nb._floating_windows[0]
        win.destroy()
        root.destroy()

    def test_close_clears_animate(self, monkeypatch):
        root = tk.Tk(); root.withdraw()
        nb = ClosableNotebook(root)
        btn = self.AnimatedButton(nb)
        nb.add(btn, text="Tab")
        nb.update_idletasks()
        self._detach(nb, monkeypatch)
        win = nb._floating_windows[0]
        win.destroy()
        root.update()
        assert "_animate" not in str(root.tk.call("after", "info"))
        root.destroy()

    def test_detach_clears_animate_without_after_info(self, monkeypatch):
        root = tk.Tk(); root.withdraw()
        nb = ClosableNotebook(root)
        btn = self.AnimatedButton(nb)
        nb.add(btn, text="Tab")
        nb.update_idletasks()

        orig_call = btn.tk.call

        def fake_call(*args):
            if args[:3] == ("after", "info", str(btn)):
                raise tk.TclError("unsupported")
            return orig_call(*args)

        monkeypatch.setattr(btn.tk, "call", fake_call)

        self._detach(nb, monkeypatch)
        root.update()
        assert "_animate" not in str(root.tk.call("after", "info"))
        win = nb._floating_windows[0]
        win.destroy()
        root.destroy()
