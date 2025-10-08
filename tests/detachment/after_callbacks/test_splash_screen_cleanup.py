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

"""Regression tests for splash screen callback cleanup."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from gui.windows.splash_screen import SplashScreen


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestSplashScreenCleanup:
    """Grouped tests ensuring splash screen timers are cancelled on close."""

    def test_close_cancels_animation_callbacks(self) -> None:
        root = tk.Tk()
        root.withdraw()
        try:
            splash = SplashScreen(root, duration=0, on_close=lambda: None)
            root.update_idletasks()
            splash._close()
            root.update()
            scheduled = root.tk.call("after", "info")
            if isinstance(scheduled, str):
                scheduled = (scheduled,)
            scheduled_repr = " ".join(map(str, scheduled))
            assert "_animate" not in scheduled_repr
            commands = getattr(root, "_tclCommands", {})
            joined = " ".join(map(str, commands))
            assert "_animate" not in joined
        finally:
            try:
                root.destroy()
            except Exception:
                pass
