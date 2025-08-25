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

import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from analysis.safety_management import SafetyManagementToolbox
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from analysis.models import global_requirements
from gui.architecture import link_requirements


def setup_toolbox():
    SysMLRepository.reset_instance()
    repo = SysMLRepository.get_instance()
    toolbox = SafetyManagementToolbox()
    gov = repo.create_diagram("Governance Diagram", name="Gov")
    toolbox.diagrams["Gov"] = gov.diag_id
    gov.objects = [
        {"obj_id": 1, "obj_type": "Work Product", "x": 0, "y": 0, "properties": {"name": "Requirement Specification"}},
        {"obj_id": 2, "obj_type": "Work Product", "x": 0, "y": 100, "properties": {"name": "Requirement Specification"}},
    ]
    gov.connections = [
        {"src": 1, "dst": 2, "stereotype": "satisfied by"}
    ]
    toolbox.add_work_product("Gov", "Requirement Specification", "")
    return toolbox


def test_requirement_spec_cannot_trace():
    tb = setup_toolbox()
    assert not tb.can_trace("Requirement Specification", "Requirement Specification")


def test_requirement_relation_governance():
    tb = setup_toolbox()
    assert tb.can_link_requirements("vehicle", "vehicle", "satisfied by")
    assert not tb.can_link_requirements("vehicle", "vehicle", "derived from")


def test_link_requirements_creates_bidirectional_relation():
    setup_toolbox()
    global_requirements.clear()
    global_requirements["R1"] = {"id": "R1", "req_type": "vehicle"}
    global_requirements["R2"] = {"id": "R2", "req_type": "vehicle"}
    link_requirements("R1", "satisfied by", "R2")
    assert {"type": "satisfied by", "id": "R2"} in global_requirements["R1"].get("relations", [])
    assert {"type": "satisfies", "id": "R1"} in global_requirements["R2"].get("relations", [])


def test_link_requirements_respects_governance():
    setup_toolbox()
    global_requirements.clear()
    global_requirements["R1"] = {"id": "R1", "req_type": "vehicle"}
    global_requirements["R2"] = {"id": "R2", "req_type": "vehicle"}
    link_requirements("R1", "derived from", "R2")
    assert "relations" not in global_requirements["R1"]


def test_non_requirement_work_product_ignored():
    SysMLRepository.reset_instance()
    repo = SysMLRepository.get_instance()
    toolbox = SafetyManagementToolbox()
    gov = repo.create_diagram("Governance Diagram", name="Gov")
    toolbox.diagrams["Gov"] = gov.diag_id
    gov.objects = [
        {"obj_id": 1, "obj_type": "Work Product", "x": 0, "y": 0, "properties": {"name": "Requirement Specification"}},
        {"obj_id": 2, "obj_type": "Work Product", "x": 0, "y": 100, "properties": {"name": "Requirement Specification"}},
        {"obj_id": 3, "obj_type": "Work Product", "x": 0, "y": 200, "properties": {"name": "Architecture Diagram"}},
    ]
    gov.connections = [
        {"src": 1, "dst": 2, "stereotype": "satisfied by"},
        {"src": 1, "dst": 3, "stereotype": "satisfied by"},
    ]
    toolbox.add_work_product("Gov", "Requirement Specification", "")
    mapping = toolbox._req_relation_mapping()
    assert mapping.get("Requirement Specification", {}).get("satisfied by") == {"Requirement Specification"}
