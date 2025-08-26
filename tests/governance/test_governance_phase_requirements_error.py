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

import types
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from gui.safety_management_toolbox import SafetyManagementWindow, SafetyManagementToolbox
from gui import safety_management_toolbox as smt
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from analysis.models import global_requirements


def test_generate_phase_requirements_handles_errors(monkeypatch):
    repo = SysMLRepository.reset_instance()
    d1 = repo.create_diagram("Governance Diagram", name="Gov1")
    t1 = repo.create_element("Action", name="Start")
    t2 = repo.create_element("Action", name="Finish")
    d1.objects = [
        {"obj_id": 1, "obj_type": "Action", "x": 0, "y": 0, "element_id": t1.elem_id, "properties": {"name": "Start"}},
        {"obj_id": 2, "obj_type": "Action", "x": 0, "y": 0, "element_id": t2.elem_id, "properties": {"name": "Finish"}},
    ]
    d1.connections = [
        {"src": 1, "dst": 2, "conn_type": "Flow", "name": "", "properties": {}}
    ]

    toolbox = SafetyManagementToolbox()
    toolbox.diagrams["Gov1"] = d1.diag_id
    mod = toolbox.add_module("Phase1")
    mod.diagrams.append("Gov1")

    win = SafetyManagementWindow.__new__(SafetyManagementWindow)
    win.toolbox = toolbox
    win.app = types.SimpleNamespace(_new_tab=lambda title: None)

    displayed = []
    def display_stub(title, ids):
        displayed.append((title, ids))
        return types.SimpleNamespace(refresh_table=lambda ids: None)
    win._display_requirements = display_stub

    errors = []
    monkeypatch.setattr(smt.messagebox, "showerror", lambda t, m: errors.append((t, m)))
    infos = []
    monkeypatch.setattr(smt.messagebox, "showinfo", lambda t, m: infos.append((t, m)))

    class BadGov:
        def generate_requirements(self):
            raise RuntimeError("model failed")

    monkeypatch.setattr(smt.GovernanceDiagram, "from_repository", lambda repo, diag_id: BadGov())

    global_requirements.clear()
    win.generate_phase_requirements("Phase1")

    assert errors and any("model failed" in msg for _, msg in errors)
    assert infos and any("No requirements were generated" in msg for _, msg in infos)
    assert not displayed
