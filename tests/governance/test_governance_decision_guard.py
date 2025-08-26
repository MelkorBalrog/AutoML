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
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from gui.architecture import SysMLObject, DiagramConnection
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from analysis.governance import GovernanceDiagram


class GovernanceDecisionGuardTests(unittest.TestCase):
    def setUp(self):
        SysMLRepository.reset_instance()
        self.repo = SysMLRepository.get_instance()

    def test_decision_flow_guard_generation(self):
        repo = self.repo
        a = repo.create_element("Action", name="A")
        b = repo.create_element("Action", name="B")
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        repo.add_element_to_diagram(diag.diag_id, a.elem_id)
        repo.add_element_to_diagram(diag.diag_id, b.elem_id)
        o1 = SysMLObject(1, "Action", 0, 0, element_id=a.elem_id)
        dec = SysMLObject(2, "Decision", 50, 0)
        o2 = SysMLObject(3, "Action", 100, 0, element_id=b.elem_id)
        diag.objects = [o1.__dict__, dec.__dict__, o2.__dict__]
        c1 = DiagramConnection(o1.obj_id, dec.obj_id, "Flow")
        c2 = DiagramConnection(dec.obj_id, o2.obj_id, "Flow")
        c2dict = c2.__dict__.copy()
        c2dict["guard"] = "g1"
        diag.connections = [c1.__dict__, c2dict]

        gdiag = GovernanceDiagram.from_repository(repo, diag.diag_id)
        self.assertIn(("A", "B"), gdiag.flows())
        self.assertEqual(gdiag.edge_data[("A", "B")]["condition"], "g1")
        reqs = gdiag.generate_requirements()
        texts = [r.text for r in reqs]
        self.assertIn("If g1, A (Action) shall precede 'B (Action)'.", texts)


if __name__ == "__main__":
    unittest.main()
