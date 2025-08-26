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

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from gui.architecture import SysMLDiagramWindow
from gui.style_manager import StyleManager


def test_governance_shapes_and_relations():
    shape = SysMLDiagramWindow._shape_for_tool
    assert shape(None, "Task") == "trapezoid"
    assert shape(None, "Vehicle") == "vehicle"
    assert shape(None, "Approves") == "relation"
    assert shape(None, "Hazard") == "hazard"
    assert shape(None, "Risk Assessment") == "clipboard"
    assert shape(None, "Safety Goal") == "shield"
    assert shape(None, "Security Threat") == "bug"
    assert shape(None, "Organization") == "building"
    assert shape(None, "Business Unit") == "department"
    assert shape(None, "Policy") == "scroll"
    assert shape(None, "Principle") == "scale"
    assert shape(None, "Guideline") == "compass"
    assert shape(None, "Standard") == "ribbon"
    assert shape(None, "Metric") == "chart"
    assert shape(None, "Safety Compliance") == "shield_check"
    assert shape(None, "Process") == "gear"
    assert shape(None, "Operation") == "wrench"
    assert shape(None, "Driving Function") == "steering"
    assert shape(None, "Plan") == "document"
    assert shape(None, "Data") == "cylinder"
    assert shape(None, "Field Data") == "cylinder"

    style = StyleManager.get_instance()
    for element in [
        "Hazard",
        "Risk Assessment",
        "Safety Goal",
        "Security Threat",
        "Organization",
        "Business Unit",
        "Policy",
        "Principle",
        "Guideline",
        "Standard",
        "Metric",
        "Safety Compliance",
        "Process",
        "Operation",
        "Driving Function",
        "Plan",
        "Data",
        "Field Data",
    ]:
        assert style.get_color(element) != "#FFFFFF"
