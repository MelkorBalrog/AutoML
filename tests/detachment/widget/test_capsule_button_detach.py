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

"""Regression tests for capsule button behaviour after tab detachment."""

from __future__ import annotations

import tkinter as tk
import pytest
from gui.utils.closable_notebook import ClosableNotebook
from gui.controls.capsule_button import CapsuleButton


@pytest.mark.skipif(CapsuleButton is None, reason="CapsuleButton unavailable")
class TestDetachedCapsuleButton:
    def _detach(self, nb: ClosableNotebook) -> CapsuleButton:
        """Detach the first tab in *nb* and return the cloned button."""
        monkey_move = lambda tab_id, target: False
        nb._move_tab = monkey_move  # type: ignore[assignment]

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        win = nb._floating_windows[0]
        new_nb = next(
            w for w in win.winfo_children() if isinstance(w, ClosableNotebook)
        )
        tab = new_nb.tabs()[0]
        return new_nb.nametowidget(tab)

    def test_hover_after_detach(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        root.report_callback_exception = lambda exc, val, tb: (_ for _ in ()).throw(val)

        nb = ClosableNotebook(root)
        btn = CapsuleButton(nb, text="ok")
        nb.add(btn, text="Tab1")
        nb.update_idletasks()

        new_btn = self._detach(nb)
        new_btn.event_generate("<Enter>", x=1, y=1)
        root.update()
        root.destroy()

    def test_motion_after_detach(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        errors: list[Exception] = []
        root.report_callback_exception = lambda exc, val, tb: errors.append(val)

        nb = ClosableNotebook(root)
        btn = CapsuleButton(nb, text="ok")
        nb.add(btn, text="Tab1")
        nb.update_idletasks()

        new_btn = self._detach(nb)
        new_btn.event_generate("<Motion>", x=1, y=1)
        root.update()
        assert not errors
        root.destroy()
