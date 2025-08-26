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

from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from analysis.safety_management import SafetyManagementToolbox


def _obj(obj_id: int, obj_type: str, name: str) -> dict:
    return {
        "obj_id": obj_id,
        "obj_type": obj_type,
        "x": 0.0,
        "y": 0.0,
        "width": 60.0,
        "height": 80.0,
        "properties": {"name": name},
    }


def test_work_product_reuse_visible():
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="GovWP")
    diag.objects.extend([
        _obj(1, "Work Product", "HAZOP"),
        _obj(2, "Lifecycle Phase", "P2"),
    ])
    diag.connections.append({"src": 2, "dst": 1, "conn_type": "Re-use"})
    toolbox = SafetyManagementToolbox()
    toolbox.diagrams = {"GovWP": diag.diag_id}
    toolbox.set_active_module("P1")
    toolbox.register_created_work_product("HAZOP", "HazDoc")
    toolbox.set_active_module("P2")
    assert toolbox.document_visible("HAZOP", "HazDoc")
    assert toolbox.document_read_only("HAZOP", "HazDoc")
    toolbox.set_active_module("P3")
    assert not toolbox.document_visible("HAZOP", "HazDoc")


def test_phase_reuse_shows_all_docs():
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="GovPhase")
    diag.objects.extend([
        _obj(1, "Lifecycle Phase", "P1"),
        _obj(2, "Lifecycle Phase", "P2"),
    ])
    diag.connections.append({"src": 2, "dst": 1, "conn_type": "Re-use"})
    toolbox = SafetyManagementToolbox()
    toolbox.diagrams = {"GovPhase": diag.diag_id}
    toolbox.set_active_module("P1")
    toolbox.register_created_work_product("FMEA", "FmeaDoc")
    toolbox.set_active_module("P2")
    assert toolbox.document_visible("FMEA", "FmeaDoc")
    assert toolbox.document_read_only("FMEA", "FmeaDoc")
    toolbox.set_active_module("P3")
    assert not toolbox.document_visible("FMEA", "FmeaDoc")

