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

"""Unit tests for :func:`gui.utils.tk_utils.reparent_widget`."""

from __future__ import annotations

import sys
import types
import tkinter as tk

import pytest

import gui.utils.tk_utils as tk_utils
from gui.utils.tk_utils import reparent_widget


@pytest.mark.detachment
@pytest.mark.reparenting
class TestReparentWidget:
    def test_uses_tk_reparent(self, monkeypatch) -> None:
        calls: list[tuple[str, str, str]] = []

        class DummyTk:
            def call(self, *args):
                calls.append(args)

        class DummyWidget:
            def __init__(self, name: str) -> None:
                self.tk = DummyTk()
                self._w = name

            def winfo_id(self) -> int:
                return 1

        w = DummyWidget(".w")
        p = DummyWidget(".p")
        reparent_widget(w, p)
        assert ("::tk::unsupported::ReparentWindow", w._w, p._w) in calls

    def test_falls_back_to_setparent(self, monkeypatch) -> None:
        called = {"SetParent": False}

        class DummyTk:
            def call(self, *args):
                raise tk.TclError("no command")

        class DummyWidget:
            def __init__(self) -> None:
                self.tk = DummyTk()
                self._w = ".w"

            def winfo_id(self) -> int:
                return 1

        def fake_setparent(wid: int, pid: int) -> int:  # pragma: no cover - mocked
            called["SetParent"] = True
            return 1

        monkeypatch.setattr(sys, "platform", "win32")
        windll = types.SimpleNamespace(user32=types.SimpleNamespace(SetParent=fake_setparent))
        monkeypatch.setattr(tk_utils.ctypes, "windll", windll, raising=False)

        w = DummyWidget()
        p = DummyWidget()
        reparent_widget(w, p)
        assert called["SetParent"]
