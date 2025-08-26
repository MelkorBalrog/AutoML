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

from gui.architecture import GovernanceDiagramWindow, SysMLObject
from analysis import SafetyManagementToolbox
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
import pytest


@pytest.mark.parametrize(
    "analysis, area_name",
    [
        ("FI2TC", "Hazard & Threat Analysis"),
        ("TC2FI", "Hazard & Threat Analysis"),
        ("Scenario Library", "Scenario"),
        ("ODD", "Scenario"),
        ("Mission Profile", "Safety Analysis"),
        ("Reliability Analysis", "Safety Analysis"),
        ("Risk Assessment", "Risk Assessment"),
    ],
)
def test_governance_work_product_enablement(analysis, area_name, monkeypatch):
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

    enable_calls = []
    captured = {}

    class DummyApp:
        safety_mgmt_toolbox = toolbox

        def enable_work_product(self, name, *, refresh=True):
            assert any(wp.analysis == name for wp in toolbox.work_products)
            enable_calls.append(name)

    win.app = DummyApp()

    class DummyDialog:
        def __init__(self, parent, title, options):
            if title == "Add Process Area":
                self.selection = area_name
            else:
                captured["options"] = options
                self.selection = analysis

    monkeypatch.setattr(GovernanceDiagramWindow, "_SelectDialog", DummyDialog)

    win.add_work_product()

    assert analysis in captured["options"]
    assert enable_calls == [analysis]
    assert any(wp.analysis == analysis for wp in toolbox.work_products)
    _sm.ACTIVE_TOOLBOX = prev_tb
