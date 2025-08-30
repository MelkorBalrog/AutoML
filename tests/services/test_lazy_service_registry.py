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
"""Tests for the lazy service registry."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mainappsrc.services.service_loader import LazyServiceRegistry
from mainappsrc.services import AnalysisUtilsService


class DummyApp:
    pass


class TestLazyServiceRegistry:
    def test_service_reloaded_after_release(self):
        """Services are re-instantiated after being released."""

        app = DummyApp()
        registry = LazyServiceRegistry(app)

        with registry.use("AnalysisUtilsService") as first:
            assert isinstance(first, AnalysisUtilsService)

        with registry.use("AnalysisUtilsService") as second:
            assert isinstance(second, AnalysisUtilsService)
            assert first is not second
        registry.shutdown()
