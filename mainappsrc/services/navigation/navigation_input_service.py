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
"""Navigation and window management service.

This service wraps :class:`~mainappsrc.core.navigation_selection_input.Navigation_Selection_Input`
for canvas and tree interactions together with
:class:`~mainappsrc.core.open_windows_features.Open_Windows_Features` for
window management helpers.  It exposes the combined interface so callers
can access both sets of functionality through a single object.
"""
from __future__ import annotations

from typing import Any

from mainappsrc.core.navigation_selection_input import Navigation_Selection_Input
from mainappsrc.core.open_windows_features import Open_Windows_Features


class NavigationInputService:
    """Delegate navigation and window operations for :class:`AutoMLApp`."""

    def __init__(self, app: Any) -> None:  # pragma: no cover - simple container
        self._navigation = Navigation_Selection_Input(app)
        self._windows = Open_Windows_Features(app)

    def __getattr__(self, name: str):
        """Delegate attribute lookups to wrapped helpers."""
        if hasattr(self._navigation, name):
            return getattr(self._navigation, name)
        return getattr(self._windows, name)


__all__ = ["NavigationInputService"]
