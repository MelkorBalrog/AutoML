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
"""Facade service bundling core application managers."""

from __future__ import annotations

from typing import Any

from mainappsrc.managers.user_manager import UserManager
from mainappsrc.managers.project_manager import ProjectManager
from mainappsrc.managers.drawing_manager import DrawingManager
from mainappsrc.managers.sotif_manager import SOTIFManager
from mainappsrc.managers.cyber_manager import CyberSecurityManager
from mainappsrc.managers.cta_manager import ControlTreeManager
from mainappsrc.managers.requirements_manager import RequirementsManagerSubApp
from mainappsrc.managers.review_manager import ReviewManager
from mainappsrc.managers.safety_case_manager import SafetyCaseManager
from mainappsrc.managers.mission_profile_manager import MissionProfileManager
from mainappsrc.managers.scenario_library_manager import ScenarioLibraryManager
from mainappsrc.managers.odd_library_manager import OddLibraryManager


class ManagersFacadeService:
    """Aggregate manager classes for simplified access."""

    def __init__(self, app: Any) -> None:  # pragma: no cover - simple container
        self.user_manager = UserManager(app)
        self.project_manager = ProjectManager(app)
        self.drawing_manager = DrawingManager(app)
        self.sotif_manager = SOTIFManager(app)
        self.cyber_manager = CyberSecurityManager(app)
        self.cta_manager = ControlTreeManager(app)
        self.requirements_manager = RequirementsManagerSubApp(app)
        self.review_manager = ReviewManager(app)
        self.safety_case_manager = SafetyCaseManager(app)
        self.mission_profile_manager = MissionProfileManager(app)
        self.scenario_library_manager = ScenarioLibraryManager(app)
        self.odd_library_manager = OddLibraryManager(app)

    def __getattr__(self, name: str):
        """Delegate attribute lookups to wrapped managers."""
        for manager in (
            self.user_manager,
            self.project_manager,
            self.drawing_manager,
            self.sotif_manager,
            self.cyber_manager,
            self.cta_manager,
            self.requirements_manager,
            self.review_manager,
            self.safety_case_manager,
            self.mission_profile_manager,
            self.scenario_library_manager,
            self.odd_library_manager,
        ):
            if hasattr(manager, name):
                return getattr(manager, name)
        raise AttributeError(name)


__all__ = ["ManagersFacadeService"]
