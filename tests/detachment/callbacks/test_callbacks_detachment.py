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

"""Grouped callback tests covering hover reset and after-event cleanup."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


pytestmark = pytest.mark.detachment


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestCallbackDetachment:
    """Grouped cases verifying hover-state reset and after-event cleanup."""

    def _setup_hover_button(self) -> tuple[tk.Tk, ClosableNotebook, tk.Button]:
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

    def test_hover_state_resets(self) -> None:
        root, nb, btn = self._setup_hover_button()
        btn.event_generate("<Enter>")
        btn.event_generate("<Leave>")
        root.update()
        assert btn["state"] == "normal"
        nb._floating_windows[0].destroy()
        root.destroy()

    class Animated(tk.Button):
        def __init__(self, master: tk.Widget) -> None:
            super().__init__(master, text="Go")
            self._spin_after = self.after(1, self._spin)

        def _spin(self) -> None:
            self._spin_after = self.after(1, self._spin)

    def test_after_callbacks_cancelled(self, capsys) -> None:
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
