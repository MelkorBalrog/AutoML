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

from gui.gsn_diagram_window import GSNDiagramWindow, GSNNode, GSNDiagram


def test_gsn_find_node_strategies():
    offset = 50

    class CanvasStub:
        def canvasx(self, x):
            return x + offset

        def canvasy(self, y):
            return y

        def find_overlapping(self, x1, y1, x2, y2):
            if x1 <= 60 <= x2 and y1 <= 10 <= y2:
                return ["id"]
            return []

        def find_closest(self, x, y):
            return ["id"]

        def bbox(self, tag):
            if tag == "id":
                return [50, 0, 70, 30]
            return None

        def gettags(self, item):
            return [item]

    node = GSNNode("A", "Goal", x=60, y=15)
    diag = GSNDiagram(node)
    win = object.__new__(GSNDiagramWindow)
    win.canvas = CanvasStub()
    win.id_to_node = {"id": node}
    win.diagram = diag
    win.zoom = 1.0

    assert win._node_at_strategy1(10, 10) is node
    assert win._node_at_strategy2(10, 10) is node
    assert win._node_at_strategy3(10, 10) is node
    assert win._node_at_strategy4(10, 10) is node
    assert win._node_at(10, 10) is node


def test_gsn_find_node_strategies_far_click():
    offset = 50

    class CanvasStub:
        def canvasx(self, x):
            return x + offset

        def canvasy(self, y):
            return y

        def find_overlapping(self, x1, y1, x2, y2):
            return []

        def find_closest(self, x, y):
            return ["id"]

        def bbox(self, tag):
            if tag == "id":
                return [50, 0, 70, 30]
            return None

        def gettags(self, item):
            return [item]

    node = GSNNode("A", "Goal", x=60, y=15)
    diag = GSNDiagram(node)
    win = object.__new__(GSNDiagramWindow)
    win.canvas = CanvasStub()
    win.id_to_node = {"id": node}
    win.diagram = diag
    win.zoom = 1.0

    assert win._node_at_strategy1(1000, 1000) is None
    assert win._node_at_strategy2(1000, 1000) is None
    assert win._node_at_strategy3(1000, 1000) is None
    assert win._node_at_strategy4(1000, 1000) is None
    assert win._node_at(1000, 1000) is None

