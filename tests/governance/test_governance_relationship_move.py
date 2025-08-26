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

import unittest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from gui.architecture import SysMLDiagramWindow, SysMLObject, DiagramConnection


class DummyCanvas:
    def canvasx(self, x):
        return x

    def canvasy(self, y):
        return y

    def delete(self, *args, **kwargs):
        pass

    def configure(self, **kwargs):
        pass


class DummyEvent:
    def __init__(self, x, y, state=0):
        self.x = x
        self.y = y
        self.state = state


class GovernanceConnectionDragTests(unittest.TestCase):
    def setUp(self):
        SysMLRepository._instance = None
        self.repo = SysMLRepository.get_instance()

    def _create_window(self):
        repo = self.repo
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        win = SysMLDiagramWindow.__new__(SysMLDiagramWindow)
        win.repo = repo
        win.diagram_id = diag.diag_id
        a = SysMLObject(1, "Work Product", 0.0, 0.0)
        b = SysMLObject(2, "Work Product", 100.0, 0.0)
        win.objects = [a, b]
        conn = DiagramConnection(a.obj_id, b.obj_id, "Flow")
        win.connections = [conn]
        win.canvas = DummyCanvas()
        win.zoom = 1.0
        win.current_tool = "Select"
        win.selected_obj = None
        win.selected_objs = []
        win.selected_conn = None
        win.dragging_point_index = None
        win.dragging_endpoint = None
        win.conn_drag_offset = None
        win.endpoint_drag_pos = None
        win.dragging_conn_mid = None
        win.dragging_conn_vec = None
        win.start = None
        win.temp_line_end = None
        win.select_rect_start = None
        win.resizing_obj = None
        win.drag_offset = (0, 0)
        win.find_connection = lambda *args, **kwargs: conn
        win.get_object = SysMLDiagramWindow.get_object.__get__(win)
        win.redraw = lambda: None
        win._sync_to_repository = lambda: None
        win.update_property_view = lambda: None
        return win, conn

    def test_connection_midpoint_drag_moves_line(self):
        win, conn = self._create_window()
        win.on_left_press(DummyEvent(50, 0))
        self.assertIsNotNone(win.dragging_conn_mid)
        self.assertEqual(conn.style, "Straight")
        win.on_left_drag(DummyEvent(60, 10))
        self.assertAlmostEqual(conn.src_pos[0], 1.0)
        self.assertAlmostEqual(conn.dst_pos[0], -1.0)
        self.assertAlmostEqual(conn.src_pos[1], 0.5)
        self.assertAlmostEqual(conn.dst_pos[1], 0.5)
        self.assertEqual(conn.points, [])


if __name__ == "__main__":
    unittest.main()
