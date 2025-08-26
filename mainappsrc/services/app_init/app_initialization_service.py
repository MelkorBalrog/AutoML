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
"""Service orchestrating application state initialisation."""

from __future__ import annotations

from ...core.app_initializer import AppInitializer
from ...managers.project_properties_manager import ProjectPropertiesManager
from ...managers.diagram_clipboard_manager import DiagramClipboardManager


class AppInitializationService:
    """Facade coordinating core initialisation helpers."""

    def __init__(self, app: object) -> None:
        self.app = app
        self._initializer = AppInitializer(app)
        self.project_properties_manager: ProjectPropertiesManager | None = None
        self.diagram_clipboard_manager: DiagramClipboardManager | None = None

    def initialize(self) -> None:
        """Run initialisation and expose created managers."""
        self._initializer.initialize()
        if not hasattr(self.app, "project_properties_manager"):
            self.app.project_properties_manager = ProjectPropertiesManager(
                self.app.project_properties
            )
        if not hasattr(self.app, "diagram_clipboard"):
            self.app.diagram_clipboard = DiagramClipboardManager(self.app)
        self.project_properties_manager = self.app.project_properties_manager
        self.diagram_clipboard_manager = self.app.diagram_clipboard

__all__ = ["AppInitializationService"]
