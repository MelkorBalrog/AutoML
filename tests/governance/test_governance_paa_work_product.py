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

from gui.architecture import GovernanceDiagramWindow
from analysis import SafetyManagementToolbox
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


def test_governance_paa_work_product_enabled(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov1")
    diag.tags.append("safety-management")

    from analysis import safety_management as _sm
    prev_tb = _sm.ACTIVE_TOOLBOX
    toolbox = SafetyManagementToolbox()

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.objects = []
    win.connections = []
    win.zoom = 1.0
    win.sort_objects = lambda: None
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None

    enabled = []
    captured = {}

    class DummyApp:
        safety_mgmt_toolbox = toolbox

        def enable_work_product(self, name, *, refresh=True):
            enabled.append(name)

    win.app = DummyApp()

    class DummyDialog:
        def __init__(self, parent, title, options):
            if title == "Add Process Area":
                self.selection = "Safety Analysis"
            else:
                captured["wp_options"] = options
                self.selection = "Prototype Assurance Analysis"

    monkeypatch.setattr(GovernanceDiagramWindow, "_SelectDialog", DummyDialog)
    win.add_work_product()

    assert "Prototype Assurance Analysis" in captured.get("wp_options", [])
    assert "Prototype Assurance Analysis" in enabled
    _sm.ACTIVE_TOOLBOX = prev_tb
