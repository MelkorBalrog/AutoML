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
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from mainappsrc.models.gsn import GSNNode, GSNDiagram
from gui.drawing_helper import GSNDrawingHelper
from gui.gsn_diagram_window import GSNDiagramWindow


class DummyCanvas:
    def __init__(self):
        self.lines = []
        self.polys = []
        self.items = 0

    def create_line(self, *pts, **kw):
        self.items += 1
        self.lines.append((pts, kw))
        return self.items

    def create_polygon(self, *pts, **kw):
        self.items += 1
        self.polys.append((pts, kw))
        return self.items

    def create_rectangle(self, *a, **k):
        pass

    def create_text(self, *a, **k):
        pass

    def bbox(self, *a, **k):
        return (0, 0, 0, 0)

    def find_withtag(self, tag):
        return []

    def itemconfigure(self, *a, **k):
        pass

    def find_overlapping(self, *a, **k):
        return []

    def gettags(self, item):
        return ()

    def tag_lower(self, *a, **k):
        pass

    def tag_raise(self, *a, **k):
        pass


def test_connection_tags_and_arrow_fill():
    helper = GSNDrawingHelper()
    canvas = DummyCanvas()
    helper.draw_solved_by_connection(canvas, (0, 0), (10, 10), obj_id="r1")
    helper.draw_in_context_connection(canvas, (0, 0), (20, 20), obj_id="r2")
    assert canvas.lines[0][1]["tags"] == ("r1",)
    assert canvas.lines[1][1]["tags"] == ("r2",)
    assert canvas.polys[0][1]["fill"] == "black"
    assert canvas.polys[0][1]["tags"] == ("r1", "r1-arrow")
    assert canvas.polys[1][1]["fill"] == "white"
    assert canvas.polys[1][1]["tags"] == ("r2", "r2-arrow")


def test_move_connection_updates_links():
    p = GSNNode("p", "Goal")
    c1 = GSNNode("c1", "Goal")
    c2 = GSNNode("c2", "Goal")
    p.add_child(c1)
    diag = GSNDiagram(p)
    diag.add_node(c1)
    diag.add_node(c2)
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    win.diagram = diag
    win.refresh = lambda: None
    win._move_connection(p, c1, c2)
    assert c1 not in p.children
    assert c2 in p.children
    assert p not in c1.parents
    assert p in c2.parents


def test_move_connection_cancelled_on_empty_drop():
    p = GSNNode("p", "Goal")
    c1 = GSNNode("c1", "Goal")
    p.add_child(c1)
    diag = GSNDiagram(p)
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    win.diagram = diag
    win.refresh = lambda: None
    # Attempt to move the connection without specifying a new child node.
    win._move_connection(p, c1, None)
    # The original relationship should remain intact.
    assert c1 in p.children
    assert p in c1.parents


def test_delete_connection_removes_links():
    p = GSNNode("p", "Goal")
    c = GSNNode("c", "Context")
    p.add_child(c, relation="context")
    diag = GSNDiagram(p)
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    win.diagram = diag
    win.refresh = lambda: None
    win._selected_connection = (p, c)
    win._on_delete(None)
    assert c not in p.children
    assert c not in p.context_children
    assert p not in c.parents
