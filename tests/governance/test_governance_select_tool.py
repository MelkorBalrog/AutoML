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
import types

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from gui.architecture import GovernanceDiagramWindow, SysMLObject
import gui.architecture as arch
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


def test_governance_diagram_has_select_button(monkeypatch):
    class DummyButton:
        def __init__(self):
            self.config: dict[str, object] = {}

        def configure(self, **kwargs):
            self.config.update(kwargs)

    def fake_sysml_init(
        self,
        master,
        title,
        tools,
        diagram_id=None,
        app=None,
        history=None,
        relation_tools=None,
        tool_groups=None,
    ):
        self.tool_buttons = {"Select": DummyButton(), "Action": DummyButton()}
        self.toolbox = types.SimpleNamespace()
        self.tools_frame = None
        self.rel_frame = None
        canvas_master = types.SimpleNamespace(
            pack_forget=lambda: None, pack=lambda **k: None
        )
        self.canvas = types.SimpleNamespace(master=canvas_master)
        self.repo = types.SimpleNamespace(diagrams={})
        self.diagram_id = "dummy"
        self.refresh_from_repository = lambda *_: None
        self.select_tool = lambda t: setattr(self, "current_tool", t)

    monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", fake_sysml_init)

    win = GovernanceDiagramWindow(None, None)
    assert "Select" in win.tool_buttons
    assert "Task" in win.tool_buttons


def test_governance_object_movable_with_select():
    class DummyCanvas:
        def canvasx(self, x):
            return x

        def canvasy(self, y):
            return y

        def configure(self, **kwargs):
            pass

        def delete(self, *args, **kwargs):
            pass

    class DummyEvent:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov")
    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    obj = SysMLObject(1, "Task", 0.0, 0.0)
    win.objects = [obj]
    win.connections = []
    win.canvas = DummyCanvas()
    win.zoom = 1.0
    win.current_tool = "Select"
    win.selected_obj = obj
    win.selected_objs = [obj]
    win.drag_offset = (0, 0)
    win.resizing_obj = None
    win.start = None
    win.select_rect_start = None
    win.dragging_point_index = None
    win.dragging_endpoint = None
    win.conn_drag_offset = None
    win.endpoint_drag_pos = None
    win.selected_conn = None
    win.app = None
    win.redraw = lambda: None
    win._sync_to_repository = lambda: None
    win.update_property_view = lambda *a, **k: None
    win.find_boundary_for_obj = lambda o: None
    win._constrain_horizontal_movement = (
        GovernanceDiagramWindow._constrain_horizontal_movement.__get__(win)
    )

    win.on_left_drag(DummyEvent(50, 20))
    assert obj.x == 50.0
    assert obj.y == 20.0
