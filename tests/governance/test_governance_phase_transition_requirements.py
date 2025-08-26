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

from analysis.governance import GovernanceDiagram


def _texts(reqs):
    texts = []
    for r in reqs:
        if isinstance(r, tuple):
            texts.append(r[0])
        elif hasattr(r, "text"):
            texts.append(r.text)
        else:
            texts.append(str(r))
    return texts


def test_phase_transition_requirement_direct_flow():
    diagram = GovernanceDiagram()
    diagram.add_task("P1", node_type="Lifecycle Phase")
    diagram.add_task("P2", node_type="Lifecycle Phase")
    diagram.add_flow("P1", "P2")

    reqs = diagram.generate_requirements()
    texts = _texts(reqs)
    assert "P1 (Lifecycle Phase) shall transition to 'P2 (Lifecycle Phase)'." in texts


def test_phase_transition_requirement_with_reuse_and_condition():
    diagram = GovernanceDiagram()
    diagram.add_task("P1", node_type="Lifecycle Phase")
    diagram.add_task("P2", node_type="Lifecycle Phase")
    diagram.add_flow("P1", "P2", "design approved")
    diagram.add_relationship("P2", "P1", conn_type="Re-use")

    reqs = diagram.generate_requirements()
    texts = _texts(reqs)
    assert (
        "P1 (Lifecycle Phase) shall transition to 'P2 (Lifecycle Phase)' reusing outputs from 'P1 (Lifecycle Phase)' only after design approved." in texts
    )
