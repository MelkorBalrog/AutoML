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

from gui.controls import messagebox
from gui.architecture import ArchitectureManagerDialog
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


def test_drop_governance_diagram_creates_action(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    src = repo.create_diagram("Governance Diagram", name="Src")
    target = repo.create_diagram("Governance Diagram", name="Target")

    mgr = ArchitectureManagerDialog.__new__(ArchitectureManagerDialog)
    mgr.repo = repo

    errors = []
    monkeypatch.setattr(messagebox, "showerror", lambda *args: errors.append(args[1]))

    mgr._drop_on_diagram(f"diag_{src.diag_id}", target)

    assert not errors
    assert any(obj["obj_type"] == "Action" for obj in target.objects)
    elem_id = next(obj["element_id"] for obj in target.objects if obj["obj_type"] == "Action")
    assert repo.elements[elem_id].elem_type == "Action"
    assert repo.get_linked_diagram(elem_id) == src.diag_id


def test_drop_non_governance_diagram_on_governance_fails(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    src = repo.create_diagram("Activity Diagram", name="Act")
    target = repo.create_diagram("Governance Diagram", name="Target")

    mgr = ArchitectureManagerDialog.__new__(ArchitectureManagerDialog)
    mgr.repo = repo

    errors = []
    monkeypatch.setattr(messagebox, "showerror", lambda *args: errors.append(args[1]))

    mgr._drop_on_diagram(f"diag_{src.diag_id}", target)

    assert errors
    assert target.objects == []
