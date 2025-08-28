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
"""Minimal FMEA service mixin to avoid circular imports."""

from __future__ import annotations


class FMEAService:
    """Lightweight FMEA helper used by :class:`SafetyAnalysis_FTA_FMEA`.

    The original project exposed a richer FMEA service from the safety
    analysis module.  During refactoring a circular import arose when the
    facade and core attempted to import each other.  This stand-alone
    mixin provides just enough structure for the core module to depend on
    without creating those cycles.
    """

    def __init__(self, app: object) -> None:
        self.app = app

    def show_fmea_list(self):  # pragma: no cover - UI delegation
        """Open the FMEA document manager if available.

        The application may supply a dedicated implementation through an
        ``editors_service`` attribute.  When absent the method simply
        returns ``None`` so tests can exercise the interface without
        requiring the full UI stack.
        """
        helper = getattr(self.app, "editors_service", None)
        if helper and hasattr(helper, "show_fmea_list"):
            return helper.show_fmea_list()
        return None


__all__ = ["FMEAService"]
