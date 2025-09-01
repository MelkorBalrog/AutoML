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

"""Verify widget interactions remain error-free after tab detachment."""

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook

try:  # pragma: no cover - CapsuleButton may be unavailable
    from gui.controls.capsule_button import CapsuleButton
except Exception:  # pragma: no cover - CapsuleButton may be unavailable
    CapsuleButton = None


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestDetachedWidgetInteraction:
    """Grouped tests for interacting with widgets in detached windows."""

    def test_clicking_widget_after_detach_has_no_invalid_command(self, monkeypatch):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        root.withdraw()
        nb = ClosableNotebook(root)
        widget = CapsuleButton(nb, text="ok") if CapsuleButton else tk.Button(nb, text="ok")
        nb.add(widget, text="Tab1")
        nb.update_idletasks()

        errors: list[str] = []
        root.report_callback_exception = lambda exc, val, tb: errors.append(str(val))
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
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        clone = new_nb.nametowidget(new_nb.tabs()[0])
        clone.event_generate("<Button-1>")
        win.update()
        assert not any("invalid command name" in e for e in errors)
        root.destroy()
