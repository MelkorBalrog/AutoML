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
from gui.architecture import SysMLObject, GovernanceDiagramWindow
from mainappsrc.models.sysml.sysml_repository import SysMLRepository, SysMLDiagram
from gui import architecture


class DummyCanvas:
    def canvasx(self, x):
        return x

    def canvasy(self, y):
        return y

    def configure(self, **kwargs):
        pass

    def create_rectangle(self, *args, **kwargs):
        return 1


class DummyEvent:
    def __init__(self, x, y, state=0):
        self.x = x
        self.y = y
        self.state = state


def test_frozen_governance_diagram_blocks_modifications(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = SysMLDiagram(diag_id="d", diag_type="Governance Diagram")
    repo.diagrams[diag.diag_id] = diag
    repo.freeze_diagram(diag.diag_id)

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.objects = []
    win.connections = []
    win.canvas = DummyCanvas()
    win.zoom = 1.0
    win.current_tool = None
    win.selected_obj = None
    win.selected_objs = []
    win.selected_conn = None
    win.drag_offset = (0, 0)
    win.resizing_obj = None
    win.start = None
    win.select_rect_start = None
    win.dragging_point_index = None
    win.dragging_endpoint = None
    win.conn_drag_offset = None
    win.endpoint_drag_pos = None
    win.app = types.SimpleNamespace()
    win.redraw = lambda: None
    win.update_property_view = lambda *a, **k: None
    win._sync_to_repository = lambda: None
    win.find_object = lambda x, y, prefer_port=False: None
    win.find_connection = lambda x, y: None

    # Selecting a tool should have no effect when diagram is read-only
    win.select_tool("Task")
    assert win.current_tool in (None, "Select")

    # Deleting objects should be blocked
    obj = SysMLObject(1, "Task", 0.0, 0.0)
    win.objects.append(obj)
    win.selected_objs = [obj]
    monkeypatch.setattr(architecture.messagebox, "askyesno", lambda *a, **k: True)
    win.remove_element_model = lambda o: win.objects.remove(o)
    win.delete_selected()
    assert obj in win.objects
