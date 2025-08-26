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

import types

from mainappsrc.models.gsn import GSNNode, GSNDiagram
from gui.safety_case_explorer import SafetyCaseExplorer
from gui.architecture import SysMLObject
from analysis.safety_management import (
    GovernanceModule,
    SafetyManagementToolbox,
    SafetyWorkProduct,
)
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


def _setup(rel=None):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov")

    toolbox = SafetyManagementToolbox()
    toolbox.diagrams = {"Gov": diag.diag_id}

    e1 = repo.create_element("Block", name="E1")
    e2 = repo.create_element("Block", name="E2")
    repo.add_element_to_diagram(diag.diag_id, e1.elem_id)
    repo.add_element_to_diagram(diag.diag_id, e2.elem_id)
    o1 = SysMLObject(1, "Work Product", 0, 0, element_id=e1.elem_id, properties={"name": "GSN Argumentation"})
    o2 = SysMLObject(2, "Work Product", 0, 100, element_id=e2.elem_id, properties={"name": "Safety & Security Case"})
    diag.objects = [o1.__dict__, o2.__dict__]
    diag.connections = [{"src": 1, "dst": 2, "conn_type": rel}] if rel else []

    toolbox.work_products = [
        SafetyWorkProduct("Gov", "GSN Argumentation", ""),
        SafetyWorkProduct("Gov", "Safety & Security Case", ""),
    ]
    toolbox.active_module = "P1"

    root = GSNNode("Diag", "Goal")
    gdiag = GSNDiagram(root)
    app = types.SimpleNamespace(
        safety_mgmt_toolbox=toolbox,
        current_review=types.SimpleNamespace(reviewed=False, approved=False),
        gsn_diagrams=[gdiag],
        gsn_modules=[],
        all_gsn_diagrams=[],
    )
    explorer = SafetyCaseExplorer.__new__(SafetyCaseExplorer)
    explorer.app = app
    return explorer, app


def test_gsn_diagram_visibility_for_safety_case():
    explorer, app = _setup()
    assert explorer._available_diagrams() == []

    explorer, app = _setup("Used By")
    assert explorer._available_diagrams()

    explorer, app = _setup("Used after Review")
    assert explorer._available_diagrams() == []
    app.current_review.reviewed = True
    assert explorer._available_diagrams()

    explorer, app = _setup("Used after Approval")
    assert explorer._available_diagrams() == []
    app.current_review.reviewed = True
    assert explorer._available_diagrams() == []
    app.current_review.approved = True
    assert explorer._available_diagrams()


def test_gsn_diagram_visibility_respects_active_phase():
    """GSN diagrams are hidden when their relation resides in another phase."""
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    gov1 = repo.create_diagram("Governance Diagram", name="Gov1")
    gov2 = repo.create_diagram("Governance Diagram", name="Gov2")

    toolbox = SafetyManagementToolbox()
    toolbox.diagrams = {"Gov1": gov1.diag_id, "Gov2": gov2.diag_id}
    toolbox.modules = [
        GovernanceModule(name="P1", diagrams=["Gov1"]),
        GovernanceModule(name="P2", diagrams=["Gov2"]),
    ]

    e1 = repo.create_element("Block", name="E1")
    e2 = repo.create_element("Block", name="E2")
    repo.add_element_to_diagram(gov2.diag_id, e1.elem_id)
    repo.add_element_to_diagram(gov2.diag_id, e2.elem_id)
    o1 = SysMLObject(1, "Work Product", 0, 0, element_id=e1.elem_id, properties={"name": "GSN Argumentation"})
    o2 = SysMLObject(2, "Work Product", 0, 100, element_id=e2.elem_id, properties={"name": "Safety & Security Case"})
    gov2.objects = [o1.__dict__, o2.__dict__]
    gov2.connections = [{"src": 1, "dst": 2, "conn_type": "Used By"}]

    toolbox.work_products = [
        SafetyWorkProduct("Gov2", "GSN Argumentation", ""),
        SafetyWorkProduct("Gov2", "Safety & Security Case", ""),
    ]
    toolbox.active_module = "P1"

    root = GSNNode("Diag", "Goal")
    gdiag = GSNDiagram(root)
    explorer = SafetyCaseExplorer.__new__(SafetyCaseExplorer)
    explorer.app = types.SimpleNamespace(
        safety_mgmt_toolbox=toolbox,
        current_review=types.SimpleNamespace(reviewed=False, approved=False),
        gsn_diagrams=[gdiag],
        gsn_modules=[],
        all_gsn_diagrams=[],
    )

    assert explorer._available_diagrams() == []
