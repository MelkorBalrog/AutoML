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

"""Service wrapper for editor dialogs and tables."""

from __future__ import annotations

from mainappsrc.core.editors import Editors


class EditorsService:
    """Facade exposing :class:`~mainappsrc.core.editors.Editors` as a service.

    The legacy :class:`Editors` class contains a collection of UI-heavy helper
    methods.  This service wraps an instance of that class and delegates attribute
    access to preserve behaviour while enabling dependency injection and future
    refactoring.
    """

    def __init__(self, app: object) -> None:
        self._impl = Editors(app)

    def __getattr__(self, name: str):
        return getattr(self._impl, name)


__all__ = ["EditorsService"]
