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


class ArrowCanvas:
    """Minimal canvas tracking rectangles for bbox() calls."""

    def __init__(self):
        self.rects = {}

    def create_rectangle(self, left, top, right, bottom, tags=()):
        if tags:
            self.rects[tags[0]] = (left, top, right, bottom)

    def create_line(self, *args, **kwargs):
        pass

    def create_text(self, *args, **kwargs):
        pass

    def create_polygon(self, *args, **kwargs):
        pass

    def bbox(self, tag):
        return self.rects.get(tag)

    def tag_lower(self, *args, **kwargs):
        pass

    def tag_raise(self, *args, **kwargs):
        pass


class ArrowHelper(GSNDrawingHelper):
    """Helper that records arrow orientation and connection points."""

    def __init__(self):
        super().__init__()
        self.arrow = None
        self.connection = None

    def draw_goal_shape(self, canvas, x, y, scale, text="", font_obj=None, obj_id=""):
        half = scale / 2
        canvas.create_rectangle(x - half, y - half, x + half, y + half, tags=(obj_id,))

    # Reuse the rectangle for other node types used in the test.
    draw_strategy_shape = draw_solution_shape = draw_goal_shape
    draw_assumption_shape = draw_goal_shape
    draw_justification_shape = draw_goal_shape
    draw_context_shape = draw_goal_shape
    draw_away_solution_shape = draw_goal_shape
    draw_away_goal_shape = draw_goal_shape
    draw_module_shape = draw_goal_shape
    draw_away_module_shape = draw_goal_shape

    def _draw_arrow(self, canvas, start_pt, end_pt, fill="black", outline="black", obj_id=""):
        self.arrow = (start_pt, end_pt)

    def draw_solved_by_connection(self, canvas, parent_pt, child_pt, obj_id=""):
        super().draw_solved_by_connection(canvas, parent_pt, child_pt, obj_id=obj_id)
        self.connection = (parent_pt, child_pt)


def test_horizontal_connection_uses_side_and_arrow_points_right():
    parent = GSNNode("p", "Goal", x=0, y=0)
    child = GSNNode("c", "Goal", x=100, y=0)
    parent.add_child(child)

    helper = ArrowHelper()
    diag = GSNDiagram(parent, drawing_helper=helper)
    diag.add_node(child)

    canvas = ArrowCanvas()
    diag.draw(canvas)

    # Connections should start/end on the sides of both shapes.
    assert helper.connection == ((30.0, 0.0), (70.0, 0.0))

    # Arrow orientation should be horizontal, pointing from parent to child.
    assert helper.arrow[0][1] == helper.arrow[1][1]
    assert helper.arrow[0][0] < helper.arrow[1][0]

