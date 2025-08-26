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

from config import load_diagram_rules


def test_governance_element_connection_rules():
    cfg = load_diagram_rules(
        Path(__file__).resolve().parents[1]
        / "config"
        / "rules"
        / "diagram_rules.json"
    )
    rules = cfg["connection_rules"]["Governance Diagram"]
    assert set(rules["Approves"]["Role"]) == {"Document", "Policy", "Procedure", "Record"}
    assert set(rules["Uses"]["Role"]) == {"Document", "Data", "Record", "Work Product"}
    assert set(rules["Executes"]["Operation"]) == {
        "Procedure",
        "Process",
        "Work Product",
    }
    assert set(rules["Executes"]["Role"]) == {
        "Procedure",
        "Process",
        "Operation",
    }
    assert set(rules["Uses"]["Operation"]) == {"Data", "Document", "Record"}
    assert set(rules["Used By"]["Guideline"]) == {"Lifecycle Phase"}
    assert set(rules["Used By"]["Policy"]) == {"Lifecycle Phase"}
    assert set(rules["Used By"]["Principle"]) == {"Lifecycle Phase"}
    assert set(rules["Used By"]["Standard"]) == {"Lifecycle Phase"}
    assert set(rules["Constrained by"]["Organization"]) == {"Policy"}
    assert set(rules["Constrained by"]["Work Product"]) == {
        "Guideline",
        "Policy",
        "Principle",
        "Standard",
        "Work Product",
    }
