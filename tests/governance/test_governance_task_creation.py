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

"""Tests for adding task elements to governance diagrams."""

import types
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from gui.architecture import GovernanceDiagramWindow


class DummyCanvas:
    def canvasx(self, x):
        return x

    def canvasy(self, y):
        return y

    def configure(self, **kwargs):
        pass


def test_task_tool_creates_action(monkeypatch):
    SysMLRepository.reset_instance()
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov")

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.zoom = 1
    win.canvas = DummyCanvas()
    win.update_property_view = lambda: None
    win.redraw = lambda: None
    win._sync_to_repository = lambda: None
    win.ensure_text_fits = lambda obj: None
    win.find_object = lambda x, y, prefer_port=False: None
    win.objects = []
    win.connections = []
    win.current_tool = "Task"
    win.start = None

    event = types.SimpleNamespace(x=0, y=0, state=0)
    GovernanceDiagramWindow.on_left_press(win, event)

    assert win.objects and win.objects[0].obj_type == "Action"
