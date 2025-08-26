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

"""Tests for lazy diagram element loading."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mainappsrc.core.diagram_renderer import DiagramRenderer


class DummyCanvas:
    def __init__(self):
        self._width = 200
        self._height = 200

    def canvasx(self, x):
        return x

    def canvasy(self, y):
        return y

    def winfo_width(self):
        return self._width

    def winfo_height(self):
        return self._height

    def delete(self, *args):
        pass

    def bbox(self, *args):
        return (0, 0, self._width, self._height)

    def config(self, **kwargs):
        pass


class DummyNode:
    def __init__(self, x, y, uid, children=None):
        self.x = x
        self.y = y
        self.unique_id = uid
        self.children = children or []
        self.parents = []
        self.is_page = False
        self.node_type = "Basic Event"
        self.gate_type = "OR"
        self.display_label = self.name = f"N{uid}"
        self.input_subtype = ""
        self.equation = self.detailed_equation = ""
        self.quant_value = None
        self.description = ""
        self.is_primary_instance = True


class DummyApp:
    def __init__(self):
        self.zoom = 1.0
        self.diagram_font = None
        self.project_properties = {}

    def get_all_nodes(self, root):
        result = [root]
        for c in root.children:
            result.extend(self.get_all_nodes(c))
        return result

    def get_node_fill_color(self, node, mode):
        return "white"


def test_lazy_loading_draws_only_visible(monkeypatch):
    app = DummyApp()
    renderer = DiagramRenderer(app)
    canvas = DummyCanvas()

    off = DummyNode(1000, 1000, 2, [])
    root = DummyNode(50, 50, 1, [off])
    off.parents = [root]

    drawn = []
    monkeypatch.setattr(renderer, "draw_node_on_canvas_pdf", lambda c, n: drawn.append(n.unique_id))
    monkeypatch.setattr(
        "mainappsrc.core.diagram_renderer.fta_drawing_helper.draw_90_connection",
        lambda *a, **k: None,
    )

    renderer.draw_subtree(canvas, root)
    assert drawn == [1]
