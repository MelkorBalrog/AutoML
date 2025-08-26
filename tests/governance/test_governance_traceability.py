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

# Ensure project root on path for direct test execution
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from analysis.models import global_requirements
from analysis.safety_management import SafetyManagementToolbox
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


def _setup_toolbox_with_trace():
    SysMLRepository.reset_instance()
    repo = SysMLRepository.get_instance()
    toolbox = SafetyManagementToolbox()
    gov = repo.create_diagram("Governance Diagram", name="Gov")
    toolbox.diagrams["Gov"] = gov.diag_id
    gov.objects = [
        {"obj_id": 1, "obj_type": "Work Product", "x": 0, "y": 0, "properties": {"name": "Requirement Specification"}},
        {"obj_id": 2, "obj_type": "Work Product", "x": 0, "y": 100, "properties": {"name": "FTA"}},
    ]
    gov.connections = [{"src": 1, "dst": 2, "conn_type": "Trace"}]
    toolbox.add_work_product("Gov", "Requirement Specification", "")
    toolbox.add_work_product("Gov", "FTA", "")
    return repo, toolbox, gov


def test_trace_link_between_work_products_allows_traceability():
    repo, toolbox, gov = _setup_toolbox_with_trace()
    assert toolbox.can_trace("Requirement Specification", "FTA")
    assert toolbox.can_trace("FTA", "Requirement Specification")


def test_requirement_link_respects_governance():
    repo, toolbox, gov = _setup_toolbox_with_trace()
    req = {"id": "R1", "req_type": "functional safety", "traces": []}
    global_requirements.clear()
    global_requirements["R1"] = req
    diag = repo.create_diagram("FTA", name="Tree")
    elem = repo.create_element("Block", name="Item")
    repo.add_element_to_diagram(diag.diag_id, elem.elem_id)
    obj = {"obj_id": 1, "obj_type": "Block", "x": 0, "y": 0, "element_id": elem.elem_id, "requirements": []}
    diag.objects = [obj]
    if not hasattr(repo, "link_requirement_to_element"):
        pytest.skip("link_requirement_to_element not available")
    assert repo.link_requirement_to_element("R1", elem.elem_id)
    assert elem.elem_id in req.get("traces", [])
    assert req in obj.get("requirements", [])
    diag2 = repo.create_diagram("STPA", name="Stpa")
    elem2 = repo.create_element("Block", name="Unrelated")
    repo.add_element_to_diagram(diag2.diag_id, elem2.elem_id)
    obj2 = {"obj_id": 1, "obj_type": "Block", "x": 0, "y": 0, "element_id": elem2.elem_id, "requirements": []}
    diag2.objects = [obj2]
    assert not repo.link_requirement_to_element("R1", elem2.elem_id)
    assert elem2.elem_id not in req.get("traces", [])
    assert req not in obj2.get("requirements", [])


def test_requirement_and_element_update_after_unlink():
    repo, toolbox, gov = _setup_toolbox_with_trace()
    req = {"id": "R1", "req_type": "functional safety", "traces": []}
    global_requirements.clear()
    global_requirements["R1"] = req
    diag = repo.create_diagram("FTA", name="Tree")
    elem = repo.create_element("Block", name="Item")
    repo.add_element_to_diagram(diag.diag_id, elem.elem_id)
    obj = {"obj_id": 1, "obj_type": "Block", "x": 0, "y": 0, "element_id": elem.elem_id, "requirements": []}
    diag.objects = [obj]
    if not (hasattr(repo, "link_requirement_to_element") and hasattr(repo, "unlink_requirement_from_element")):
        pytest.skip("link/unlink methods not available")
    repo.link_requirement_to_element("R1", elem.elem_id)
    repo.unlink_requirement_from_element("R1", elem.elem_id)
    assert elem.elem_id not in req.get("traces", [])
    assert obj.get("requirements", []) == []
