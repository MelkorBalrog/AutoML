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

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from analysis.safety_management import SafetyManagementToolbox


def test_copied_work_product_governs_active_phase():
    SysMLRepository.reset_instance()
    repo = SysMLRepository.get_instance()

    # Original diagram in Phase1 declaring Control Flow Diagram work product
    repo.active_phase = "Phase1"
    gov1 = repo.create_diagram("Governance Diagram", name="Gov1")
    gov1.tags.append("safety-management")
    gov1.objects = [
        {
            "obj_id": 1,
            "obj_type": "Work Product",
            "x": 0.0,
            "y": 0.0,
            "properties": {"name": "Control Flow Diagram"},
        }
    ]

    toolbox = SafetyManagementToolbox()
    toolbox.diagrams["Gov1"] = gov1.diag_id
    toolbox.add_work_product("Gov1", "Control Flow Diagram", "")

    # Copy of the work product in Phase2 without explicit declaration
    repo.active_phase = "Phase2"
    gov2 = repo.create_diagram("Governance Diagram", name="Gov2")
    gov2.tags.append("safety-management")
    gov2.objects = [
        {
            "obj_id": 2,
            "obj_type": "Work Product",
            "x": 0.0,
            "y": 0.0,
            "properties": {"name": "Control Flow Diagram"},
        }
    ]
    toolbox.diagrams["Gov2"] = gov2.diag_id

    toolbox.set_active_module("Phase2")

    assert toolbox.enabled_products() == {"Control Flow Diagram"}
