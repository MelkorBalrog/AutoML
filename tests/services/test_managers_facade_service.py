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
"""Tests for :mod:`ManagersFacadeService`."""

from __future__ import annotations

import sys
from pathlib import Path
from contextlib import contextmanager, ExitStack
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mainappsrc.services.managers import ManagersFacadeService

MANAGER_PATH = "mainappsrc.services.managers.managers_facade_service"


@contextmanager
def _patch_managers():
    names = [
        "UserManager",
        "ProjectManager",
        "DrawingManager",
        "SOTIFManager",
        "CyberSecurityManager",
        "ControlTreeManager",
        "RequirementsManagerSubApp",
        "ReviewManager",
        "SafetyCaseManager",
        "MissionProfileManager",
        "ScenarioLibraryManager",
        "OddLibraryManager",
    ]
    with ExitStack() as stack:
        mocks = {
            name: stack.enter_context(patch(f"{MANAGER_PATH}.{name}", MagicMock()))
            for name in names
        }
        yield mocks


class TestManagersFacadeService:
    def test_initializes_all_managers(self):
        app = object()
        with _patch_managers() as mocks:
            ManagersFacadeService(app)
            for mock in mocks.values():
                mock.assert_called_once_with(app)

    def test_delegates_attribute_lookup(self):
        app = object()
        with _patch_managers() as mocks:
            user = mocks["UserManager"].return_value
            user.greet.return_value = 42
            service = ManagersFacadeService(app)
            assert service.greet() == 42
            user.greet.assert_called_once_with()
