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

from dataclasses import asdict
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from gui.architecture import SysMLObject, DiagramConnection
from analysis.safety_management import SafetyManagementToolbox, GovernanceModule
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


def test_governance_elements_visible_all_phases():
    repo = SysMLRepository.reset_instance()
    toolbox = SafetyManagementToolbox()
    toolbox.modules = [GovernanceModule("P1"), GovernanceModule("P2")]
    toolbox.set_active_module("P1")

    diag = repo.create_diagram("Governance Diagram", name="Gov")
    diag.tags.append("safety-management")

    obj1 = SysMLObject(1, "Work Product", 0.0, 0.0)
    diag.objects.append(asdict(obj1))

    toolbox.set_active_module("P2")
    obj2 = SysMLObject(2, "Work Product", 0.0, 0.0)
    diag.objects.append(asdict(obj2))

    conn = DiagramConnection(obj1.obj_id, obj2.obj_id, "Flow")
    diag.connections.append(asdict(conn))

    toolbox.set_active_module("P1")
    assert repo.diagram_visible(diag.diag_id)
    assert diag.diag_id in repo.visible_diagrams()
    assert len(repo.visible_objects(diag.diag_id)) == 2
    assert len(repo.visible_connections(diag.diag_id)) == 1

    toolbox.set_active_module("P2")
    assert repo.diagram_visible(diag.diag_id)
    assert diag.diag_id in repo.visible_diagrams()
    assert len(repo.visible_objects(diag.diag_id)) == 2
    assert len(repo.visible_connections(diag.diag_id)) == 1

