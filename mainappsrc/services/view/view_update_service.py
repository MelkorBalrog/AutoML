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
"""Service wrapping :mod:`view_updater` utilities."""

from __future__ import annotations

from ...core.view_updater import ViewUpdater


class ViewUpdateService:
    """Facade delegating project view refreshes to :class:`ViewUpdater`."""

    def __init__(self, app: object) -> None:
        self._updater = ViewUpdater(app)

    def update_views(self) -> None:
        """Refresh project views via the underlying updater."""
        self._updater.update_views()


__all__ = ["ViewUpdateService"]
