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
"""Tests for :mod:`AnalysisUtilsService`."""

import types

from mainappsrc.services.analysis.analysis_utils_service import AnalysisUtilsService
from mainappsrc.services.safety_analysis import SafetyAnalysisService


def test_service_wraps_probability_and_utils():
    app = types.SimpleNamespace(
        scenario_libraries=[{"scenarios": [{"name": "use", "tcs": False}, {"name": "sotif", "type": "sotif"}]}],
        mechanism_libraries=[],
        selected_mechanism_libraries=[],
    )
    service = AnalysisUtilsService(app)
    assert isinstance(service.probability_reliability, SafetyAnalysisService)
    groups = service.classify_scenarios()
    assert groups["use_case"] == ["use"]
    assert groups["sotif"] == ["sotif"]
    service.load_default_mechanisms()
    names = {lib.name for lib in app.mechanism_libraries}
    assert "ISO 26262 Annex D" in names
    assert "PAS 8800" in names
