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

from AutoML import AutoMLApp
from mainappsrc.managers.undo_manager import UndoRedoManager
from mainappsrc.core.navigation_selection_input import Navigation_Selection_Input


class DummyEvent:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def test_drag_records_only_endpoints_and_undo_redo():
    app = AutoMLApp.__new__(AutoMLApp)
    app.zoom = 1.0
    app.grid_size = 1
    node = types.SimpleNamespace(
        x=0.0,
        y=0.0,
        node_type="Block",
        children=[],
        is_primary_instance=True,
    )
    app.root_node = node
    app.get_all_nodes = lambda root: [node]
    app.move_subtree = lambda n, dx, dy: None
    app.sync_nodes_by_id = lambda n: None
    app.redraw_canvas = lambda: None
    app.undo_manager = UndoRedoManager(app)
    app.nav_input = Navigation_Selection_Input(app)
    app.export_model_data = lambda include_versions=False: {
        "diagrams": [{"objects": [{"x": node.x, "y": node.y}]}]
    }
    app.apply_model_data = lambda data: (
        setattr(node, "x", data["diagrams"][0]["objects"][0]["x"]),
        setattr(node, "y", data["diagrams"][0]["objects"][0]["y"]),
    )
    app.push_undo_state = AutoMLApp.push_undo_state.__get__(app)
    app.undo = AutoMLApp.undo.__get__(app)
    app.redo = AutoMLApp.redo.__get__(app)
    app.on_canvas_click = AutoMLApp.on_canvas_click.__get__(app)
    app.on_canvas_drag = AutoMLApp.on_canvas_drag.__get__(app)
    app.on_canvas_release = AutoMLApp.on_canvas_release.__get__(app)
    app.canvas = types.SimpleNamespace(canvasx=lambda x: x, canvasy=lambda y: y)
    app.diagram_tabs = {}
    app.refresh_all = lambda: None

    app.on_canvas_click(DummyEvent(0, 0))
    app.on_canvas_drag(DummyEvent(10, 10))
    app.on_canvas_release(DummyEvent(10, 10))

    assert node.x == 10.0 and node.y == 10.0
    assert len(app.undo_manager._undo_stack) == 2

    app.undo()
    assert node.x == 0.0 and node.y == 0.0

    app.redo()
    assert node.x == 10.0 and node.y == 10.0


def test_multiple_drags_undo_step_by_step():
    app = AutoMLApp.__new__(AutoMLApp)
    app.zoom = 1.0
    app.grid_size = 1
    node = types.SimpleNamespace(
        x=0.0,
        y=0.0,
        node_type="Block",
        children=[],
        is_primary_instance=True,
    )
    app.root_node = node
    app.get_all_nodes = lambda root: [node]
    app.move_subtree = lambda n, dx, dy: None
    app.sync_nodes_by_id = lambda n: None
    app.redraw_canvas = lambda: None
    app.undo_manager = UndoRedoManager(app)
    app.nav_input = Navigation_Selection_Input(app)
    app.export_model_data = lambda include_versions=False: {
        "diagrams": [{"objects": [{"x": node.x, "y": node.y}]}]
    }
    app.apply_model_data = lambda data: (
        setattr(node, "x", data["diagrams"][0]["objects"][0]["x"]),
        setattr(node, "y", data["diagrams"][0]["objects"][0]["y"]),
    )
    app.push_undo_state = AutoMLApp.push_undo_state.__get__(app)
    app.undo = AutoMLApp.undo.__get__(app)
    app.redo = AutoMLApp.redo.__get__(app)
    app.on_canvas_click = AutoMLApp.on_canvas_click.__get__(app)
    app.on_canvas_drag = AutoMLApp.on_canvas_drag.__get__(app)
    app.on_canvas_release = AutoMLApp.on_canvas_release.__get__(app)
    app.canvas = types.SimpleNamespace(canvasx=lambda x: x, canvasy=lambda y: y)
    app.diagram_tabs = {}
    app.refresh_all = lambda: None

    # First drag to (10, 10)
    app.on_canvas_click(DummyEvent(0, 0))
    app.on_canvas_drag(DummyEvent(10, 10))
    app.on_canvas_release(DummyEvent(10, 10))

    # Second drag to (20, 20)
    app.on_canvas_click(DummyEvent(10, 10))
    app.on_canvas_drag(DummyEvent(20, 20))
    app.on_canvas_release(DummyEvent(20, 20))

    assert node.x == 20.0 and node.y == 20.0
    assert len(app.undo_manager._undo_stack) == 3

    app.undo()
    assert node.x == 10.0 and node.y == 10.0

    app.undo()
    assert node.x == 0.0 and node.y == 0.0

    app.redo()
    assert node.x == 10.0 and node.y == 10.0

    app.redo()
    assert node.x == 20.0 and node.y == 20.0
