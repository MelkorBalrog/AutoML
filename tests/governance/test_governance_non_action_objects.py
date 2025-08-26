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

from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from analysis.governance import GovernanceDiagram


def test_requirements_with_non_action_objects():
    repo = SysMLRepository.reset_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov")
    ann = repo.create_element("ANN", name="ANN1")
    gate = repo.create_element("Decision", name="Gate")
    diag.objects = [
        {"obj_id": 1, "obj_type": "ANN", "element_id": ann.elem_id, "properties": {"name": "ANN1"}},
        {"obj_id": 2, "obj_type": "Decision", "element_id": gate.elem_id, "properties": {"name": "Gate"}},
    ]
    diag.connections = [
        {"src": 2, "dst": 1, "conn_type": "AI training", "name": "data ready", "properties": {}}
    ]

    gov = GovernanceDiagram.from_repository(repo, diag.diag_id)
    reqs = gov.generate_requirements()
    assert any("Gate" in r and "ANN1" in r for r in reqs)
