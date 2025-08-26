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

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from analysis.governance import GovernanceDiagram


def test_decision_transition_requirement_mentions_source():
    diagram = GovernanceDiagram()
    diagram.add_task("Collect Data", node_type="Task")
    diagram.add_task("Decision1", node_type="Decision")
    diagram.add_task("ANN1", node_type="ANN")
    diagram.add_flow("Collect Data", "Decision1")
    diagram.add_relationship(
        "Decision1",
        "ANN1",
        conn_type="AI training",
        condition="completion >= 0.98",
    )

    reqs = diagram.generate_requirements()
    texts = [r.text for r in reqs]
    assert "If completion >= 0.98, after 'Collect Data (Task)', Engineering team shall train 'ANN1 (ANN)'." in texts
    assert all("Decision1" not in t for t in texts)
