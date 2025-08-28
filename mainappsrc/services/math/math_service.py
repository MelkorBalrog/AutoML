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
"""Math service delegating arithmetic to the C API DLL."""

from __future__ import annotations

from mainappsrc.core import api


class MathService:
    """Expose arithmetic helpers backed by the core C API."""

    @staticmethod
    def add(left: int, right: int) -> int:
        """Return the sum of two integers via the DLL-backed API."""
        return api.add(left, right)


__all__ = ["MathService"]
