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
import types

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from AutoML import AutoMLApp
from mainappsrc.models.gsn import GSNNode, GSNDiagram
from mainappsrc.core.syncing_and_ids import Syncing_And_IDs
from mainappsrc.services.syncing import SyncingAndIdsService


class DummyEvent:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def _make_app_with_clone():
    root = GSNNode("A", "Goal", x=0, y=0)
    clone = root.clone()
    clone.x = 50
    clone.y = 60
    diag = GSNDiagram(root)
    diag.add_node(clone)

    app = AutoMLApp.__new__(AutoMLApp)
    app.root_node = root
    app.get_all_nodes = types.MethodType(lambda self, _=None: [root, clone], app)
    app.get_all_fmea_entries = types.MethodType(lambda self: [], app)
    app.zoom = 1.0
    app.grid_size = 1
    app.canvas = types.SimpleNamespace(canvasx=lambda x: x, canvasy=lambda y: y)
    app.move_subtree = lambda *args: None
    app.redraw_canvas = lambda: None
    app.syncing_service = SyncingAndIdsService(app)

    def nav_drag(event):
        node = app.dragging_node
        node.x = event.x
        node.y = event.y
        app.sync_nodes_by_id(node)

    app.nav_input = types.SimpleNamespace(
        on_canvas_drag=nav_drag,
        on_canvas_release=lambda _e: None,
    )
    return app, root, clone


def test_dragging_clone_preserves_original_coordinates():
    app, root, clone = _make_app_with_clone()

    coords_during_sync = {}
    original_sync = AutoMLApp.sync_nodes_by_id.__get__(app)

    def sync_wrapper(node):
        coords_during_sync["val"] = (node.x, node.y)
        return original_sync(node)

    app.sync_nodes_by_id = sync_wrapper
    app.dragging_node = clone
    app.drag_offset_x = 0
    app.drag_offset_y = 0

    app.on_canvas_drag(DummyEvent(150, 160))

    assert coords_during_sync["val"] == (150, 160)
    assert (root.x, root.y) == (0, 0)
    assert (clone.x, clone.y) == (150, 160)


def test_dragging_original_preserves_clone_coordinates():
    app, root, clone = _make_app_with_clone()
    app.dragging_node = root
    app.drag_offset_x = 0
    app.drag_offset_y = 0

    app.on_canvas_drag(DummyEvent(100, 120))

    assert (root.x, root.y) == (100, 120)
    assert (clone.x, clone.y) == (50, 60)


def test_sync_nodes_by_id_excludes_coordinates():
    app, root, _ = _make_app_with_clone()
    captured_attrs = {}
    orig = Syncing_And_IDs._sync_nodes_by_id_strategy1

    def capture(self, updated_node, attrs):
        captured_attrs["attrs"] = list(attrs)
        return orig(self, updated_node, attrs)

    impl = app.syncing_service._impl
    impl._sync_nodes_by_id_strategy1 = types.MethodType(capture, impl)
    app.syncing_service.sync_nodes_by_id(root)
    assert "x" not in captured_attrs["attrs"]
    assert "y" not in captured_attrs["attrs"]
