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

"""Tests for cancelling lingering Tk ``after`` callbacks."""

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestCancelAfterEvents:
    """Grouped tests covering ``cancel_after_events`` edge cases."""

    def test_cancel_after_events_cancels_widget_after(self) -> None:
        root = tk.Tk()
        root.withdraw()
        btn = tk.Button(root)
        ident = btn.after(1000000, lambda: None)
        nb = ClosableNotebook(root)
        nb._cancel_after_events(btn)
        assert ident not in btn.tk.call("after", "info", str(btn))
        root.destroy()

    def test_cancel_after_events_handles_animation_identifier_attribute(self) -> None:
        root = tk.Tk()
        root.withdraw()
        frame = tk.Frame(root)
        nb = ClosableNotebook(root)
        ident = frame.after(10_000, lambda: None)
        frame._explorer_animation_id = ident  # type: ignore[attr-defined]
        nb._cancel_after_events(frame)
        scheduled = str(frame.tk.call("after", "info"))
        assert ident not in scheduled
        root.destroy()

    def test_cancel_after_events_handles_animate_id_suffix(self) -> None:
        root = tk.Tk()
        root.withdraw()
        frame = tk.Frame(root)
        nb = ClosableNotebook(root)
        ident = frame.after(10_000, lambda: None)
        frame._animate_id = ident  # type: ignore[attr-defined
        nb._cancel_after_events(frame)
        scheduled = str(frame.tk.call("after", "info"))
        assert ident not in scheduled
        root.destroy()

    def test_cancel_after_events_handles_dictionary_values(self) -> None:
        root = tk.Tk()
        root.withdraw()
        frame = tk.Frame(root)
        nb = ClosableNotebook(root)
        ident = frame.after(10_000, lambda: None)
        frame._timer_handles = {"pulse": ident}  # type: ignore[attr-defined]
        nb._cancel_after_events(frame)
        scheduled = str(frame.tk.call("after", "info"))
        assert ident not in scheduled
        root.destroy()

    def test_cancel_after_events_handles_callable_animation(self) -> None:
        root = tk.Tk()
        root.withdraw()
        nb = ClosableNotebook(root)

        class AnimatedFrame(tk.Frame):
            def start(self) -> None:
                self.after(10_000, self._animate)

            def _animate(self) -> None:  # pragma: no cover - requires tkinter callback
                self.after(10_000, self._animate)

        frame = AnimatedFrame(root)
        frame.start()
        nb._cancel_after_events(frame)
        scheduled = str(frame.tk.call("after", "info"))
        assert "_animate" not in scheduled
        root.destroy()
