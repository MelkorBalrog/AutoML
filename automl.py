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

"""Lowercase convenience alias for the :mod:`AutoML` launcher."""

# Re-export everything from the canonical ``AutoML`` module so legacy imports
# using ``import automl`` continue to work.  Tests rely on functions such as
# ``ensure_ghostscript`` and ``ensure_packages`` being available at module level.
from AutoML import *  # noqa: F401,F403
from AutoML import __all__  # noqa: F401

