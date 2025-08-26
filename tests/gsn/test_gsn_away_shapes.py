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

import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from mainappsrc.models.gsn.nodes import GSNNode
from mainappsrc.models.gsn.diagram import GSNDiagram
from gui.drawing_helper import GSNDrawingHelper

class StubCanvas:
    def __init__(self):
        self.items = []
    def create_rectangle(self, *args, **kwargs):
        self.items.append(("rect", args, kwargs))
    def create_arc(self, *args, **kwargs):
        self.items.append(("arc", args, kwargs))
    def create_text(self, *args, **kwargs):
        self.items.append(("text", args, kwargs))
    def create_line(self, *args, **kwargs):
        self.items.append(("line", args, kwargs))
    def create_polygon(self, *args, **kwargs):
        self.items.append(("poly", args, kwargs))
    def bbox(self, tag):
        return None
    def tag_lower(self, *args, **kwargs):
        pass
    def tag_raise(self, *args, **kwargs):
        pass

class RecordingHelper:
    def __init__(self):
        self.calls = []
    def get_text_size(self, text, font_obj):
        return len(text) * 5, 10
    def draw_away_goal_shape(self, canvas, x, y, scale, text="", module_text="", font_obj=None, obj_id=""):
        self.calls.append(("goal", module_text))
    def draw_away_solution_shape(self, canvas, x, y, scale, text="", module_text="", font_obj=None, obj_id=""):
        self.calls.append(("solution", module_text))
    def draw_away_context_shape(self, canvas, x, y, scale, text="", module_text="", font_obj=None, obj_id=""):
        self.calls.append(("context", module_text))
    def draw_away_assumption_shape(self, canvas, x, y, scale, text="", module_text="", font_obj=None, obj_id=""):
        self.calls.append(("assumption", module_text))
    def draw_away_justification_shape(self, canvas, x, y, scale, text="", module_text="", font_obj=None, obj_id=""):
        self.calls.append(("justification", module_text))
    # Unused stubs
    def draw_goal_shape(self, canvas, x, y, scale, text="", module_text="", font_obj=None, obj_id=""):
        self.calls.append(("goal_primary", module_text))
    def draw_solution_shape(self, *a, **k):
        pass
    def draw_module_shape(self, *a, **k):
        pass
    def draw_assumption_shape(self, *a, **k):
        pass
    def draw_justification_shape(self, *a, **k):
        pass
    def draw_context_shape(self, *a, **k):
        pass
    def draw_solved_by_connection(self, *a, **k):
        pass
    def draw_in_context_connection(self, *a, **k):
        pass
    def point_on_shape(self, shape, target_pt):
        return target_pt

@pytest.mark.parametrize("node_type,expected", [
    ("Goal", "goal"),
    ("Solution", "solution"),
    ("Context", "context"),
    ("Assumption", "assumption"),
    ("Justification", "justification"),
])
def test_away_shapes_receive_module_identifier(node_type, expected):
    module = GSNNode("Mod", "Module")
    original = GSNNode("Orig", node_type)
    original.parents.append(module)
    clone = GSNNode("Clone", node_type, is_primary_instance=False, original=original)
    helper = RecordingHelper()
    diag = GSNDiagram(clone, drawing_helper=helper)
    canvas = StubCanvas()
    diag.draw(canvas)
    assert helper.calls[0] == (expected, "Mod")


def test_away_shapes_without_module_identifier():
    original = GSNNode("Orig", "Goal")
    clone = GSNNode("Clone", "Goal", is_primary_instance=False, original=original)
    helper = RecordingHelper()
    diag = GSNDiagram(clone, drawing_helper=helper)
    canvas = StubCanvas()
    diag.draw(canvas)
    assert helper.calls[0] == ("goal", "")


def test_goal_clone_with_original_but_primary_flag_draws_away_shape():
    original = GSNNode("Orig", "Goal")
    clone = GSNNode("Clone", "Goal", original=original)
    helper = RecordingHelper()
    diag = GSNDiagram(clone, drawing_helper=helper)
    canvas = StubCanvas()
    diag.draw(canvas)
    assert helper.calls[0][0] == "goal"


class DummyFont:
    def measure(self, text):
        return len(text) * 5

    def metrics(self, _):
        return 10


def test_away_solution_module_box_adjacent():
    helper = GSNDrawingHelper()
    helper.get_text_size = lambda text, font: (len(text) * 5, 10)
    helper._scaled_font = lambda scale: DummyFont()
    canvas = StubCanvas()
    helper.draw_away_solution_shape(
        canvas,
        0,
        0,
        scale=60,
        text="S",
        module_text="M",
        font_obj=DummyFont(),
    )
    rects = [item for item in canvas.items if item[0] == "rect"]
    assert len(rects) >= 2
    outer = rects[0][1]
    box = rects[1][1]
    outer_bottom = outer[3]
    box_top = box[1]
    assert abs(box_top - outer_bottom) <= 1


def test_module_box_defaults_to_root():
    helper = GSNDrawingHelper()
    helper.get_text_size = lambda text, font: (len(text) * 5, 10)
    helper._scaled_font = lambda scale: DummyFont()
    canvas = StubCanvas()
    helper.draw_away_solution_shape(
        canvas,
        0,
        0,
        scale=60,
        text="S",
        module_text="",
        font_obj=DummyFont(),
    )
    texts = [item for item in canvas.items if item[0] == "text"]
    assert any(kwargs.get("text") == "root" for _type, args, kwargs in texts)
