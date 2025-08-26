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
from mainappsrc.models.gsn import GSNNode, GSNDiagram
from AutoML import AutoMLApp


def test_moving_gsn_clone_preserves_original_position():
    root = GSNNode("A", "Goal", x=0, y=0)
    diag = GSNDiagram(root)
    clone = root.clone()
    clone.x = 50
    clone.y = 60
    diag.add_node(clone)
    root.display_label = ""
    clone.display_label = ""

    def get_all_nodes(self, _):
        return [root, clone]

    def get_all_fmea(self):
        return []

    app = object.__new__(AutoMLApp)
    app.root_node = root
    app.get_all_nodes = types.MethodType(get_all_nodes, app)
    app.get_all_fmea_entries = types.MethodType(get_all_fmea, app)

    # move clone
    clone.x += 100
    clone.y += 100
    AutoMLApp.sync_nodes_by_id(app, clone)

    assert (root.x, root.y) == (0, 0)
    assert (clone.x, clone.y) == (150, 160)


def test_moving_gsn_original_preserves_clone_position():
    root = GSNNode("A", "Goal", x=0, y=0)
    clone = root.clone()
    clone.x = 50
    clone.y = 60
    diag = GSNDiagram(root)
    diag.add_node(clone)
    root.display_label = ""
    clone.display_label = ""

    def get_all_nodes(self, _):
        return [root, clone]

    def get_all_fmea(self):
        return []

    app = object.__new__(AutoMLApp)
    app.root_node = root
    app.get_all_nodes = types.MethodType(get_all_nodes, app)
    app.get_all_fmea_entries = types.MethodType(get_all_fmea, app)

    root.x += 100
    root.y += 100
    AutoMLApp.move_subtree(app, root, 100, 100)
    AutoMLApp.sync_nodes_by_id(app, root)

    assert (clone.x, clone.y) == (50, 60)
    assert (root.x, root.y) == (100, 100)


def test_moving_parent_with_clone_child_keeps_clone_static():
    root = GSNNode("A", "Goal", x=0, y=0)
    clone = root.clone(root)
    clone.x = 50
    clone.y = 60
    diag = GSNDiagram(root)
    diag.add_node(clone)
    root.display_label = ""
    clone.display_label = ""

    def get_all_nodes(self, _):
        return [root, clone]

    def get_all_fmea(self):
        return []

    app = object.__new__(AutoMLApp)
    app.root_node = root
    app.get_all_nodes = types.MethodType(get_all_nodes, app)
    app.get_all_fmea_entries = types.MethodType(get_all_fmea, app)

    root.x += 10
    root.y += 20
    AutoMLApp.move_subtree(app, root, 10, 20)
    AutoMLApp.sync_nodes_by_id(app, root)

    assert (root.x, root.y) == (10, 20)
    assert (clone.x, clone.y) == (50, 60)
