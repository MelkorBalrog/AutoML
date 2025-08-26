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
"""Compatibility wrapper for :mod:`mainappsrc.core.page_diagram`.

Exposes the :class:`PageDiagram` API at the historic module location to keep
imports working across the codebase and test suite.
"""
from mainappsrc.core.page_diagram import *  # noqa: F401,F403
from mainappsrc.core.page_diagram import fta_drawing_helper  # noqa: F401
