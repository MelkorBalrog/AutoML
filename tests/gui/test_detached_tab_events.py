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
"""Grouped tests verifying callbacks in detached tab widgets."""

from __future__ import annotations

import tkinter as tk
import pytest

from gui.utils.closable_notebook import ClosableNotebook


class TestDetachedTabEvents:
    """Detach a tab and ensure callbacks fire in the new window."""

    def _detach(self, nb: ClosableNotebook) -> tk.Widget:
        monkey_move = lambda tab_id, target: False
        nb._move_tab = monkey_move  # type: ignore[assignment]

        class Event: ...

        press = Event()
        press.x = 5
        press.y = 5
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

    def test_hover_callbacks_fire(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        events: list[str] = []
        nb = ClosableNotebook(root)
        btn = tk.Button(nb, text="hi")
        btn.bind("<Enter>", lambda _e: events.append("enter"))
        btn.bind("<Leave>", lambda _e: events.append("leave"))
        nb.add(btn, text="T1")
        nb.update_idletasks()

        new_btn = self._detach(nb)
        new_btn.event_generate("<Enter>", x=1, y=1)
        root.update()
        new_btn.event_generate("<Leave>", x=1, y=1)
        root.update()
        assert events == ["enter", "leave"]
        root.destroy()

    def test_click_callbacks_fire(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        clicks: list[str] = []
        nb = ClosableNotebook(root)
        btn = tk.Button(nb, text="hi")
        btn.bind("<Button-1>", lambda _e: clicks.append("click"))
        nb.add(btn, text="T1")
        nb.update_idletasks()

        new_btn = self._detach(nb)
        new_btn.event_generate("<Button-1>", x=1, y=1)
        root.update()
        assert clicks == ["click"]
        root.destroy()
