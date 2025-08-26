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

from analysis.governance import GovernanceDiagram, GeneratedRequirement


@pytest.mark.parametrize(
    "conn_type, action",
    [
        ("Re-use", "re-use"),
        ("Propagate", "propagate"),
        ("Propagate by Review", "propagate by review"),
        ("Propagate by Approval", "propagate by approval"),
        ("Used By", "be used by"),
        ("Used after Review", "be used after review"),
        ("Used after Approval", "be used after approval"),
        ("Trace", "trace to"),
        ("Satisfied by", "be satisfied by"),
        ("Derived from", "be derived from"),
    ],
)
def test_generate_requirements_for_additional_relationships(conn_type, action):
    diagram = GovernanceDiagram()
    diagram.add_task("Source")
    diagram.add_task("Target")
    diagram.add_relationship("Source", "Target", conn_type=conn_type)

    reqs = [r for r in diagram.generate_requirements() if isinstance(r, GeneratedRequirement)]
    assert any(r.action == action for r in reqs)
