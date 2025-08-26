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
"""Tests for :mod:`WindowControllersService`."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mainappsrc.services.windows import WindowControllersService
from mainappsrc.core.event_dispatcher import EventDispatcher
from gui.controls.window_controllers import WindowControllers
from mainappsrc.core.top_event_workflows import Top_Event_Workflows


def test_lazy_initialisation() -> None:
    """Service lazily creates wrapped helpers."""
    service = WindowControllersService(SimpleNamespace())
    assert isinstance(service.event_dispatcher, EventDispatcher)
    assert isinstance(service.window_controllers, WindowControllers)
    assert isinstance(service.top_event_workflows, Top_Event_Workflows)


def test_prompt_user_info(monkeypatch) -> None:
    """User info dialog results are returned."""
    results = ("Alice", "a@example.com")

    class DummyDialog:
        def __init__(self, parent, name, email):
            self.result = results

    with patch(
        "mainappsrc.services.windows.window_controllers_service.UserInfoDialog",
        DummyDialog,
    ):
        parent = object()
        assert (
            WindowControllersService.prompt_user_info(parent, "n", "e")
            == results
        )
