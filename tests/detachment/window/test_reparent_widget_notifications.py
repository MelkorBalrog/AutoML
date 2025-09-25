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

"""Regression tests for notifying Tk after reparenting widgets."""

from __future__ import annotations

import types
import tkinter as tk

import pytest

from gui.utils import tk_utils


class _DummyTk:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def call(self, *args: str) -> None:
        self.calls.append(tuple(str(a) for a in args))
        if args and args[0] == "tk::unsupported::reparent":
            raise tk.TclError("unsupported")


class _DummyWidget:
    def __init__(self, widget_id: int) -> None:
        self._id = widget_id
        self.tk = _DummyTk()
        self.master = object()

    def update_idletasks(self) -> None:  # pragma: no cover - trivial
        return

    def winfo_id(self) -> int:
        return self._id


@pytest.mark.detachment
@pytest.mark.reparenting
class TestTkReparentNotifications:
    def test_linux_reparent_notifies_tk(self, monkeypatch: pytest.MonkeyPatch) -> None:
        widget = _DummyWidget(10)
        parent = _DummyWidget(20)

        monkeypatch.setattr(tk_utils.sys, "platform", "linux")

        called: dict[str, object] = {}

        class _FakeX11:
            def XOpenDisplay(self, _name: object) -> int:
                called["open"] = True
                return 1

            def XReparentWindow(
                self, display: int, wid: int, pid: int, x: int, y: int
            ) -> None:
                called["reparent"] = (display, wid, pid, x, y)

            def XFlush(self, display: int) -> None:
                called["flush"] = display

            def XCloseDisplay(self, display: int) -> None:
                called["close"] = display

        monkeypatch.setattr(
            tk_utils.ctypes,
            "cdll",
            types.SimpleNamespace(LoadLibrary=lambda _name: _FakeX11()),
        )

        counter = {"count": 0}
        monkeypatch.setattr(
            tk_utils,
            "_notify_tk_reparent",
            lambda w, p: counter.__setitem__("count", counter["count"] + 1),
        )

        tk_utils.reparent_widget(widget, parent)

        assert counter["count"] == 1
        assert called["reparent"] == (1, widget.winfo_id(), parent.winfo_id(), 0, 0)

    def test_windows_reparent_notifies_tk(self, monkeypatch: pytest.MonkeyPatch) -> None:
        widget = _DummyWidget(11)
        parent = _DummyWidget(21)

        monkeypatch.setattr(tk_utils.sys, "platform", "win32")

        class _FakeUser32:
            def __init__(self) -> None:
                self.calls: list[tuple[int, int]] = []

            def SetParent(self, wid: int, pid: int) -> int:
                self.calls.append((wid, pid))
                return 1

        fake_user32 = _FakeUser32()
        monkeypatch.setattr(
            tk_utils.ctypes,
            "windll",
            types.SimpleNamespace(user32=fake_user32),
            raising=False,
        )

        counter = {"count": 0}
        monkeypatch.setattr(
            tk_utils,
            "_notify_tk_reparent",
            lambda w, p: counter.__setitem__("count", counter["count"] + 1),
        )

        tk_utils.reparent_widget(widget, parent)

        assert counter["count"] == 1
        assert fake_user32.calls == [(widget.winfo_id(), parent.winfo_id())]
