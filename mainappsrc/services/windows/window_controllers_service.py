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
"""Service wrapper for window-related helpers.

The :class:`WindowControllersService` lazily instantiates window management
helpers and provides convenience wrappers so the core application can access
these utilities through a single interface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mainappsrc.core.event_dispatcher import EventDispatcher
from gui.controls.window_controllers import WindowControllers
from mainappsrc.core.top_event_workflows import Top_Event_Workflows
from gui.dialogs.user_info_dialog import UserInfoDialog

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from mainappsrc.core.automl_core import AutoMLApp


class WindowControllersService:
    """Central access point for window helpers and dialogs."""

    def __init__(self, app: AutoMLApp) -> None:
        self.app = app

    # ------------------------------------------------------------------
    # Lazy accessors
    @property
    def event_dispatcher(self) -> EventDispatcher:
        if not hasattr(self, "_event_dispatcher"):
            self._event_dispatcher = EventDispatcher(self.app)
        return self._event_dispatcher

    @property
    def window_controllers(self) -> WindowControllers:
        if not hasattr(self, "_window_controllers"):
            self._window_controllers = WindowControllers(self.app)
        return self._window_controllers

    @property
    def top_event_workflows(self) -> Top_Event_Workflows:
        if not hasattr(self, "_top_event_workflows"):
            self._top_event_workflows = Top_Event_Workflows(self.app)
        return self._top_event_workflows

    # ------------------------------------------------------------------
    # Convenience helpers
    def register_events(self) -> None:
        """Register keyboard shortcuts and tab events."""
        dispatcher = self.event_dispatcher
        dispatcher.register_keyboard_shortcuts()
        dispatcher.register_tab_events()

    @staticmethod
    def prompt_user_info(parent, name: str = "", email: str = ""):
        """Prompt for the user's name and email."""
        dialog = UserInfoDialog(parent, name, email)
        return dialog.result
