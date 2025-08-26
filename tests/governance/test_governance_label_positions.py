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
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from gui.architecture import (
    _BOTTOM_LABEL_TYPES,
    GovernanceDiagramWindow,
    SysMLRepository,
    SysMLObject,
)


class DummyCanvas:
    def canvasx(self, x):
        return x

    def canvasy(self, y):
        return y


def test_governance_names_after_shape():
    for obj_type in ("Organization", "Model", "Business Unit"):
        assert obj_type in _BOTTOM_LABEL_TYPES


def test_bottom_label_shapes_fixed_size():
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram")
    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.zoom = 1.0
    win.canvas = DummyCanvas()
    win.start = None
    win.current_tool = "Select"
    win.select_rect_start = None
    win.dragging_endpoint = None
    win.selected_conn = None
    win.dragging_point_index = None
    win.conn_drag_offset = None
    for obj_type in ("Organization", "Model", "Business Unit"):
        obj = SysMLObject(
            1,
            obj_type,
            0.0,
            0.0,
            width=80.0,
            height=40.0,
            properties={"name": obj_type},
        )
        win.objects = [obj]
        win.selected_obj = obj
        assert win.hit_resize_handle(obj, 0.0, 0.0) is None
        win.resizing_obj = obj
        win.resize_edge = "se"
        event = types.SimpleNamespace(x=100, y=100)
        win.on_left_drag(event)
        assert obj.width == 80.0
        assert obj.height == 40.0
