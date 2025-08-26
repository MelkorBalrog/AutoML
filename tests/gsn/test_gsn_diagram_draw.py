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
        self.items = []

    def create_rectangle(self, left, top, right, bottom, **kw):
        self.items.append((left, top, right, bottom, kw))

    def create_line(self, *args, **kwargs):
        pass

    def create_text(self, *args, **kwargs):
        pass

    def bbox(self, tag):
        for left, top, right, bottom, kw in self.items:
            if kw.get("tags") == (tag,):
                return left, top, right, bottom
        return None

    def tag_lower(self, *args, **kwargs):
        pass

    def tag_raise(self, *args, **kwargs):
        pass


class DummyHelper:
    def draw_goal_shape(self, canvas, x, y, scale, obj_id=""):
        left = x - scale / 2
        top = y - scale / 2
        right = x + scale / 2
        bottom = y + scale / 2
        canvas.create_rectangle(left, top, right, bottom, tags=(obj_id,))

    draw_strategy_shape = draw_goal_shape
    draw_solution_shape = draw_goal_shape
    draw_away_solution_shape = draw_goal_shape
    draw_away_goal_shape = draw_goal_shape
    draw_assumption_shape = draw_goal_shape
    draw_justification_shape = draw_goal_shape
    draw_context_shape = draw_goal_shape
    draw_module_shape = draw_goal_shape
    draw_away_module_shape = draw_goal_shape

    def draw_solved_by_connection(self, *args, **kwargs):
        pass

    def draw_in_context_connection(self, *args, **kwargs):
        pass

    def point_on_shape(self, shape, target_pt):
        return target_pt

    def get_text_size(self, text, font_obj):
        lines = text.split("\n")
        width = max(len(line) for line in lines) * 5
        height = 10 * len(lines)
        return width, height


def _rect_for(node_id, canvas):
    for left, top, right, bottom, kw in canvas.items:
        if kw.get("tags") == (node_id,):
            return left, top, right, bottom, kw
    raise KeyError(node_id)


def test_draw_tags_and_zoom_scaling():
    root = GSNNode("Root", "Goal", x=10, y=10)
    diag = GSNDiagram(root, drawing_helper=DummyHelper())

    c1 = StubCanvas()
    diag.draw(c1, zoom=1.0)
    rect1 = _rect_for(root.unique_id, c1)

    c2 = StubCanvas()
    diag.draw(c2, zoom=2.0)
    rect2 = _rect_for(root.unique_id, c2)

    assert rect2[0] == rect1[0] * 2
    assert rect1[4]["tags"] == (root.unique_id,)


def test_draw_respects_context_links():
    """Context links are rendered with the correct connector style."""
    root = GSNNode("Root", "Goal")
    child = GSNNode("Child", "Context")
    root.add_child(child, relation="context")
    diag = GSNDiagram(root, drawing_helper=DummyHelper())
    diag.add_node(child)

    calls = []

    def solved(*args, **kwargs):
        calls.append("solved")

    def ctx(*args, **kwargs):
        calls.append("context")

    diag.drawing_helper.draw_solved_by_connection = solved
    diag.drawing_helper.draw_in_context_connection = ctx
    diag.draw(StubCanvas())
    assert calls == ["context"]


def test_solution_circle_expands_with_text(monkeypatch):
    """Solution nodes enlarge their circle to fit the text."""
    class StubFont:
        def __init__(self, *a, **k):
            pass

        def measure(self, text):
            return len(text) * 5

        def metrics(self, key):  # pragma: no cover - simple helper
            return 10

    monkeypatch.setattr("gsn.diagram.tkFont.Font", lambda *a, **k: StubFont())

    node = GSNNode("Sol", "Solution", x=10, y=10, description="long text " * 10)
    diag = GSNDiagram(node, drawing_helper=DummyHelper())
    canvas = StubCanvas()
    diag.draw(canvas)
    rect = _rect_for(node.unique_id, canvas)
    assert rect[2] - rect[0] > 40


class _StubFont:
    def __init__(self, width=5, linespace=10):
        self._width = width
        self._linespace = linespace

    def measure(self, text):
        return len(text) * self._width

    def metrics(self, key):  # pragma: no cover - simple helper
        return self._linespace


def test_wrap_text_limits_line_width():
    diag = GSNDiagram(GSNNode("Root", "Goal"), drawing_helper=DummyHelper())
    font = _StubFont()
    long = "word " * 20
    wrapped = diag._wrap_text(long.strip(), font, 50)
    assert "\n" in wrapped
    for line in wrapped.split("\n"):
        assert font.measure(line) <= 50
