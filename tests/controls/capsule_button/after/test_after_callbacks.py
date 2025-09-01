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

"""Grouped tests confirming ``after`` callbacks do not fire after detachment."""

from __future__ import annotations

import os
import tkinter as tk
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[4]))

import pytest

from gui.controls.capsule_button import CapsuleButton
from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestCapsuleButtonAfterDetach:
    """Ensure scheduled callbacks are cancelled during detachment."""

    def _setup(self) -> tuple[tk.Tk, ClosableNotebook, CapsuleButton]:
        root = tk.Tk(); root.withdraw()
        nb = ClosableNotebook(root)
        btn = CapsuleButton(nb, text="Demo")
        nb.add(btn, text="Tab")
        nb.update_idletasks()
        return root, nb, btn

    def _detach(self, nb: ClosableNotebook, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(nb, "_move_tab", lambda tab_id, target: False)

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

    def test_root_after_cancelled(self, monkeypatch) -> None:
        root, nb, btn = self._setup()
        fired = False

        def cb(arg: str) -> None:
            nonlocal fired
            fired = True

        cmd = root.register(cb)
        ident = btn.tk.call("after", "1", f"{cmd} {btn}")
        self._detach(nb, monkeypatch)
        root.update()
        info = btn.tk.call("after", "info")
        if isinstance(info, str):
            info = [info]
        assert ident not in info
        assert not fired
        nb._floating_windows[0].destroy()
        root.destroy()

    def test_widget_after_cancelled(self, monkeypatch) -> None:
        root, nb, btn = self._setup()
        fired = False

        def cb() -> None:
            nonlocal fired
            fired = True

        ident = btn.after(1, cb)
        self._detach(nb, monkeypatch)
        root.update()
        info = btn.tk.call("after", "info")
        if isinstance(info, str):
            info = [info]
        assert ident not in info
        assert not fired
        nb._floating_windows[0].destroy()
        root.destroy()
