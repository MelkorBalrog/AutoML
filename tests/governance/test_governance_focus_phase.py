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

"""Tests for reactivating governance diagram phases on focus."""

import types
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from analysis.safety_management import SafetyManagementToolbox, GovernanceModule
from gui.architecture import GovernanceDiagramWindow


class DummyCanvas:
    def canvasx(self, x):
        return x

    def canvasy(self, y):
        return y

    def configure(self, **kwargs):
        pass


def test_focus_reactivates_phase_allows_edit():
    repo = SysMLRepository.reset_instance()
    toolbox = SafetyManagementToolbox()
    toolbox.modules = [GovernanceModule("P1"), GovernanceModule("P2")]
    toolbox.set_active_module("P1")
    diag = repo.create_diagram("Governance Diagram", name="Gov")
    repo.set_diagram_phase(diag.diag_id, "P1")

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.app = types.SimpleNamespace(safety_mgmt_toolbox=toolbox)
    win.zoom = 1
    win.canvas = DummyCanvas()
    win.update_property_view = lambda: None
    win.redraw = lambda: None
    win._sync_to_repository = lambda: None
    win.find_object = lambda x, y, prefer_port=False: None
    win.ensure_text_fits = lambda obj: None
    win.font = types.SimpleNamespace(measure=lambda text: 0)
    win.objects = []
    win.connections = []

    toolbox.set_active_module("P2")
    win._on_focus_in()
    assert repo.active_phase == "P1"
    win.select_tool("Task")
    GovernanceDiagramWindow.on_left_press(win, types.SimpleNamespace(x=0, y=0, state=0))

    assert win.objects and win.objects[0].obj_type == "Action"
