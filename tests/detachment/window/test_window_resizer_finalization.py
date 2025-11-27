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

"""Finalization safety for the window resize controller."""

from __future__ import annotations

import gui.utils.window_resizer as window_resizer


class _StubWindow:
    def __init__(self) -> None:
        self.unbind_calls: list[tuple[tuple[str, str], dict[str, str]]] = []

    def wm_resizable(self, *_args, **_kwargs) -> None:  # pragma: no cover - noop
        return None

    def bind(self, *args, **_kwargs) -> str:  # pragma: no cover - basic stub
        return f"bind-{args[0]}"

    def unbind(self, *args, **kwargs) -> None:  # pragma: no cover - tracking only
        self.unbind_calls.append((args, kwargs))

    def winfo_id(self) -> None:  # pragma: no cover - disable Win32 hook install
        return None


def test_shutdown_skips_finalizing(monkeypatch) -> None:
    """Ensure shutdown avoids Tk/Win32 work during interpreter finalization."""

    win = _StubWindow()
    monkeypatch.setattr(window_resizer, "_python_is_finalizing", lambda: False)
    controller = window_resizer.WindowResizeController(win)
    monkeypatch.setattr(window_resizer, "_python_is_finalizing", lambda: True)

    controller.shutdown()

    assert win.unbind_calls == []

