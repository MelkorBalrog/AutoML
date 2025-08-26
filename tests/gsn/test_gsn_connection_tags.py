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

from mainappsrc.models.gsn import GSNNode, GSNDiagram


class StubCanvas:
    def __init__(self):
        self.lines = []
        self.polys = []

    def create_line(self, *args, **kwargs):
        self.lines.append(kwargs.get("tags"))

    def create_polygon(self, *args, **kwargs):
        self.polys.append(kwargs.get("tags"))

    def create_text(self, *args, **kwargs):
        pass

    def create_rectangle(self, *args, **kwargs):
        pass

    def bbox(self, tag):
        return None

    def tag_lower(self, *args, **kwargs):
        pass

    def tag_raise(self, *args, **kwargs):
        pass


class DummyHelper:
    def draw_solved_by_connection(self, canvas, parent_pt, child_pt, obj_id=""):
        canvas.create_line(0, 0, 0, 0, tags=(obj_id,))
        canvas.create_polygon([], tags=(obj_id,))

    def draw_in_context_connection(self, *args, **kwargs):
        pass


def test_connection_tags_present():
    parent = GSNNode("P", "Goal")
    child = GSNNode("C", "Goal")
    parent.add_child(child, relation="solved")
    diag = GSNDiagram(parent, drawing_helper=DummyHelper())
    diag.add_node(child)
    diag._draw_node = lambda *a, **k: None  # avoid tkinter font
    canvas = StubCanvas()
    diag.draw(canvas)
    tag = f"{parent.unique_id}->{child.unique_id}"
    assert canvas.lines[0] == (tag,)
    assert canvas.polys[0] == (tag,)
