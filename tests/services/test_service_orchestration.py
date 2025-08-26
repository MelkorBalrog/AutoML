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
"""Integration tests verifying service orchestration."""

from __future__ import annotations

from mainappsrc.automl_core import AutoMLApp
from mainappsrc import services

user_config_service = services.user_config_service


class TestAnalysisServices:
    def test_analysis_utils_delegation(self):
        """AutoMLApp delegates analysis tasks to its service."""

        class DummyService:
            def __init__(self) -> None:
                self.classified = False
                self.loaded = False

            def classify_scenarios(self):
                self.classified = True

            def load_default_mechanisms(self):
                self.loaded = True

        app = AutoMLApp.__new__(AutoMLApp)
        service = DummyService()
        app.analysis_utils_service = service

        app.classify_scenarios()
        app.load_default_mechanisms()

        assert service.classified and service.loaded


class TestUserConfigService:
    def test_set_current_user(self):
        """User configuration updates propagate through the service."""
        name = "Tester"
        email = "tester@example.com"
        user_config_service.set_current_user(name, email)
        assert user_config_service.current_user_name == name
        assert user_config_service.current_user_email == email

class TestServiceRegistry:
    def test_all_service_classes_resolvable(self):
        """Every service listed in the registry is accessible."""

        for name in services.SERVICE_CLASSES:
            assert hasattr(services, name)
