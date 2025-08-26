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
import unittest
from dataclasses import asdict

sys.path.append(str(Path(__file__).resolve().parents[1]))

from gui.architecture import GovernanceDiagramWindow, SysMLObject, SysMLDiagramWindow
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


class GovernanceDecisionPhaseFlowTests(unittest.TestCase):
    def setUp(self):
        SysMLRepository.reset_instance()
        self.repo = SysMLRepository.get_instance()

    def _window(self, diag):
        class Win:
            _decision_used_corners = SysMLDiagramWindow._decision_used_corners

            def __init__(self, repo, diagram_id):
                self.repo = repo
                self.diagram_id = diagram_id
                self.connections = []

        return Win(self.repo, diag.diag_id)

    def test_decision_to_phase_flow_allowed(self):
        repo = self.repo
        dec_elem = repo.create_element("Decision", name="Gate")
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        repo.add_element_to_diagram(diag.diag_id, dec_elem.elem_id)
        decision = SysMLObject(
            1,
            "Decision",
            0.0,
            0.0,
            element_id=dec_elem.elem_id,
            properties={"name": "Gate"},
        )
        phase = SysMLObject(2, "Lifecycle Phase", 0.0, 100.0, properties={"name": "P2"})
        diag.objects = [asdict(decision), asdict(phase)]
        win = self._window(diag)
        valid, _ = GovernanceDiagramWindow.validate_connection(win, decision, phase, "Flow")
        self.assertTrue(valid)
        valid, _ = GovernanceDiagramWindow.validate_connection(win, phase, decision, "Flow")
        self.assertTrue(valid)


if __name__ == "__main__":
    unittest.main()

