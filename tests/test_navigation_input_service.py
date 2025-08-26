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

import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from mainappsrc.services.navigation import NavigationInputService
from mainappsrc.core.open_windows_features import Open_Windows_Features
from mainappsrc.core.navigation_selection_input import Navigation_Selection_Input


def test_service_delegates_to_open_windows(monkeypatch):
    called = {}

    def fake_open(self):
        called["flag"] = True

    monkeypatch.setattr(Open_Windows_Features, "open_reliability_window", fake_open)

    svc = NavigationInputService(types.SimpleNamespace())
    svc.open_reliability_window()
    assert called["flag"] is True


def test_service_delegates_to_navigation(monkeypatch):
    called = {}

    def fake_back(self):
        called["flag"] = True

    monkeypatch.setattr(Navigation_Selection_Input, "go_back", fake_back)

    svc = NavigationInputService(types.SimpleNamespace())
    svc.go_back()
    assert called["flag"] is True
