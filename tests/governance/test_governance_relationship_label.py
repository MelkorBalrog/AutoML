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


def test_label_relationship_between_database_nodes():
    diagram = GovernanceDiagram()
    diagram.add_task("User DB")
    diagram.add_task("Analytics DB")
    diagram.add_relationship("User DB", "Analytics DB", label="sync with")

    assert diagram.edge_data[("User DB", "Analytics DB")]["label"] == "sync with"

    reqs = diagram.generate_requirements()
    texts = [r.text for r in reqs]
    assert "User DB (Action) shall sync with 'Analytics DB (Action)'." in texts

