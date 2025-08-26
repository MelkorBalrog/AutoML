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

from mainappsrc.models.gsn import GSNNode


def test_invalid_solved_relationship_ignored_on_load():
    parent_data = {
        "unique_id": "1",
        "user_name": "G",
        "node_type": "Goal",
        # legacy data erroneously lists an Assumption in children
        "children": ["2"],
    }
    assumption_data = {
        "unique_id": "2",
        "user_name": "A",
        "node_type": "Assumption",
    }
    nodes = {}
    parent = GSNNode.from_dict(parent_data, nodes)
    assumption = GSNNode.from_dict(assumption_data, nodes)

    # Should not raise even though relationship is invalid
    GSNNode.resolve_references(nodes)

    assert assumption not in parent.children
    assert parent not in assumption.parents


def test_invalid_context_relationship_ignored_on_load():
    parent_data = {
        "unique_id": "1",
        "user_name": "G1",
        "node_type": "Goal",
        # legacy model incorrectly links another Goal via context
        "context": ["2"],
    }
    goal_child_data = {
        "unique_id": "2",
        "user_name": "G2",
        "node_type": "Goal",
    }
    nodes = {}
    parent = GSNNode.from_dict(parent_data, nodes)
    goal_child = GSNNode.from_dict(goal_child_data, nodes)

    # Should not raise, invalid context link skipped
    GSNNode.resolve_references(nodes)

    assert goal_child not in parent.context_children
    assert parent not in goal_child.parents
